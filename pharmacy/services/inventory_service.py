"""Medicine inventory CRUD, stock adjustment, and expiry monitoring service."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from pharmacy.config import DEFAULT_EXPIRY_WARNING_DAYS, DEFAULT_LOW_STOCK_THRESHOLD
from pharmacy.database.db_manager import DatabaseManager
from pharmacy.models.entities import Medicine, StockAdjustment
from pharmacy.utils import (
    BusinessRuleError,
    ValidationError,
    now_timestamp,
    parse_iso_date,
    parse_non_negative_float,
    parse_non_negative_int,
    parse_positive_float,
    parse_positive_int,
    today_date,
    today_iso,
    validate_non_empty,
)


class InventoryService:
    """Manages medicine catalog, stock adjustments, low-stock and expiry filters."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    @staticmethod
    def _row_to_medicine(row: sqlite3.Row) -> Medicine:
        return Medicine(
            id=row["id"],
            name=row["name"],
            generic_name=row["generic_name"],
            category=row["category"],
            batch_number=row["batch_number"],
            supplier_id=row["supplier_id"],
            cost_price=float(row["cost_price"]),
            unit_price=float(row["unit_price"]),
            quantity=int(row["quantity"]),
            reorder_level=int(row["reorder_level"]),
            expiry_date=row["expiry_date"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            supplier_name=row["supplier_name"] or "Unassigned",
        )

    def list_medicines(
        self,
        search_query: str = "",
        status_filter: str = "all",
        warning_days: int = DEFAULT_EXPIRY_WARNING_DAYS,
    ) -> list[Medicine]:
        """List medicines with optional text search and status filter.

        status_filter: 'all', 'low_stock', 'expiring_soon', 'expired', 'available_for_sale'
        """
        query = f"%{(search_query or '').strip()}%"
        today = today_date()
        today_str = today.isoformat()
        warn_str = (today + timedelta(days=max(1, int(warning_days)))).isoformat()

        clauses = [
            "(m.name LIKE ? OR m.generic_name LIKE ? OR m.category LIKE ? OR m.batch_number LIKE ? OR COALESCE(s.name, '') LIKE ?)"
        ]
        params: list[object] = [query, query, query, query, query]

        if status_filter == "low_stock":
            clauses.append("m.quantity <= m.reorder_level")
        elif status_filter == "expired":
            clauses.append("m.expiry_date <= ?")
            params.append(today_str)
        elif status_filter == "expiring_soon":
            clauses.append("m.expiry_date > ? AND m.expiry_date <= ?")
            params.extend([today_str, warn_str])
        elif status_filter == "available_for_sale":
            clauses.append("m.quantity > 0 AND m.expiry_date > ?")
            params.append(today_str)

        where_sql = " AND ".join(clauses)
        sql = f"""
            SELECT m.*, s.name AS supplier_name
            FROM medicines m
            LEFT JOIN suppliers s ON s.id = m.supplier_id
            WHERE {where_sql}
            ORDER BY m.name COLLATE NOCASE ASC, m.expiry_date ASC
        """
        rows = self.db.connection.execute(sql, params).fetchall()
        return [self._row_to_medicine(row) for row in rows]

    def get_medicine(self, medicine_id: int) -> Medicine | None:
        """Fetch a single medicine by ID."""
        row = self.db.connection.execute(
            """
            SELECT m.*, s.name AS supplier_name
            FROM medicines m
            LEFT JOIN suppliers s ON s.id = m.supplier_id
            WHERE m.id = ?
            """,
            (medicine_id,),
        ).fetchone()
        return self._row_to_medicine(row) if row else None

    def _validate_supplier_exists(self, supplier_id: int | None) -> int | None:
        if supplier_id is None:
            return None
        row = self.db.connection.execute(
            "SELECT id FROM suppliers WHERE id = ?", (supplier_id,)
        ).fetchone()
        if not row:
            raise ValidationError(f"Selected supplier (#{supplier_id}) does not exist.")
        return int(row["id"])

    def create_medicine(
        self,
        name: str,
        batch_number: str,
        unit_price: object,
        quantity: object,
        expiry_date: str,
        generic_name: str = "",
        category: str = "General",
        supplier_id: int | None = None,
        cost_price: object = 0.0,
        reorder_level: object = DEFAULT_LOW_STOCK_THRESHOLD,
        description: str = "",
    ) -> Medicine:
        """Validate and insert a new medicine batch."""
        clean_name = validate_non_empty(name, "Medicine name")
        clean_batch = validate_non_empty(batch_number, "Batch number").upper()
        clean_category = (category or "").strip() or "General"
        parsed_cost = parse_non_negative_float(cost_price, "Cost price")
        parsed_price = parse_positive_float(unit_price, "Unit price")
        parsed_qty = parse_non_negative_int(quantity, "Quantity")
        parsed_reorder = parse_non_negative_int(reorder_level, "Reorder level")
        parsed_expiry = parse_iso_date(expiry_date, "Expiry date").isoformat()
        valid_supplier_id = self._validate_supplier_exists(supplier_id)
        now = now_timestamp()

        try:
            with self.db.transaction() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO medicines (
                        name, generic_name, category, batch_number, supplier_id,
                        cost_price, unit_price, quantity, reorder_level, expiry_date,
                        description, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        clean_name,
                        (generic_name or "").strip(),
                        clean_category,
                        clean_batch,
                        valid_supplier_id,
                        parsed_cost,
                        parsed_price,
                        parsed_qty,
                        parsed_reorder,
                        parsed_expiry,
                        (description or "").strip(),
                        now,
                        now,
                    ),
                )
                med_id = int(cur.lastrowid)
                if parsed_qty > 0:
                    conn.execute(
                        """
                        INSERT INTO stock_adjustments (medicine_id, change_qty, reason, reference_note, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (med_id, parsed_qty, "Initial Stock", f"Batch {clean_batch}", now),
                    )
        except sqlite3.IntegrityError as exc:
            raise ValidationError(
                f"Batch number '{clean_batch}' already exists in inventory."
            ) from exc

        created = self.get_medicine(med_id)
        assert created is not None
        return created

    def update_medicine(
        self,
        medicine_id: int,
        name: str,
        batch_number: str,
        unit_price: object,
        quantity: object,
        expiry_date: str,
        generic_name: str = "",
        category: str = "General",
        supplier_id: int | None = None,
        cost_price: object = 0.0,
        reorder_level: object = DEFAULT_LOW_STOCK_THRESHOLD,
        description: str = "",
    ) -> Medicine:
        """Validate and update an existing medicine record."""
        existing = self.get_medicine(medicine_id)
        if not existing:
            raise ValidationError(f"Medicine #{medicine_id} was not found.")

        clean_name = validate_non_empty(name, "Medicine name")
        clean_batch = validate_non_empty(batch_number, "Batch number").upper()
        clean_category = (category or "").strip() or "General"
        parsed_cost = parse_non_negative_float(cost_price, "Cost price")
        parsed_price = parse_positive_float(unit_price, "Unit price")
        parsed_qty = parse_non_negative_int(quantity, "Quantity")
        parsed_reorder = parse_non_negative_int(reorder_level, "Reorder level")
        parsed_expiry = parse_iso_date(expiry_date, "Expiry date").isoformat()
        valid_supplier_id = self._validate_supplier_exists(supplier_id)
        now = now_timestamp()
        qty_delta = parsed_qty - existing.quantity

        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE medicines
                    SET name = ?, generic_name = ?, category = ?, batch_number = ?,
                        supplier_id = ?, cost_price = ?, unit_price = ?, quantity = ?,
                        reorder_level = ?, expiry_date = ?, description = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        clean_name,
                        (generic_name or "").strip(),
                        clean_category,
                        clean_batch,
                        valid_supplier_id,
                        parsed_cost,
                        parsed_price,
                        parsed_qty,
                        parsed_reorder,
                        parsed_expiry,
                        (description or "").strip(),
                        now,
                        medicine_id,
                    ),
                )
                if qty_delta != 0:
                    conn.execute(
                        """
                        INSERT INTO stock_adjustments (medicine_id, change_qty, reason, reference_note, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            medicine_id,
                            qty_delta,
                            "Manual Edit",
                            f"Updated from {existing.quantity} to {parsed_qty}",
                            now,
                        ),
                    )
        except sqlite3.IntegrityError as exc:
            raise ValidationError(
                f"Another medicine already uses batch number '{clean_batch}'."
            ) from exc

        updated = self.get_medicine(medicine_id)
        assert updated is not None
        return updated

    def adjust_stock(
        self,
        medicine_id: int,
        delta: object,
        reason: str = "Restock",
        reference_note: str = "",
    ) -> Medicine:
        """Increment or decrement medicine stock atomically with audit logging."""
        try:
            change_qty = int(str(delta).strip())
        except (TypeError, ValueError) as exc:
            raise ValidationError("Stock adjustment quantity must be a whole number.") from exc

        if change_qty == 0:
            raise ValidationError("Stock adjustment quantity cannot be zero.")

        clean_reason = validate_non_empty(reason, "Adjustment reason")
        now = now_timestamp()

        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT id, name, quantity FROM medicines WHERE id = ?",
                (medicine_id,),
            ).fetchone()
            if not row:
                raise ValidationError(f"Medicine #{medicine_id} was not found.")

            new_qty = int(row["quantity"]) + change_qty
            if new_qty < 0:
                raise BusinessRuleError(
                    f"Cannot reduce '{row['name']}' below 0 (current stock: {row['quantity']})."
                )

            conn.execute(
                "UPDATE medicines SET quantity = ?, updated_at = ? WHERE id = ?",
                (new_qty, now, medicine_id),
            )
            conn.execute(
                """
                INSERT INTO stock_adjustments (medicine_id, change_qty, reason, reference_note, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (medicine_id, change_qty, clean_reason, (reference_note or "").strip(), now),
            )

        updated = self.get_medicine(medicine_id)
        assert updated is not None
        return updated

    def restock_medicine(
        self, medicine_id: int, add_qty: object, reference_note: str = ""
    ) -> Medicine:
        """Add positive stock quantity to an existing batch."""
        qty = parse_positive_int(add_qty, "Restock quantity")
        return self.adjust_stock(
            medicine_id=medicine_id,
            delta=qty,
            reason="Restock",
            reference_note=reference_note,
        )

    def write_off_expired_stock(self, medicine_id: int) -> Medicine:
        """Zero out remaining quantity of an expired batch with an audit record."""
        med = self.get_medicine(medicine_id)
        if not med:
            raise ValidationError(f"Medicine #{medicine_id} was not found.")
        if med.expiry_date > today_iso():
            raise BusinessRuleError(
                f"'{med.name}' (Batch {med.batch_number}) is not expired yet."
            )
        if med.quantity == 0:
            raise BusinessRuleError(
                f"'{med.name}' (Batch {med.batch_number}) already has 0 stock."
            )
        return self.adjust_stock(
            medicine_id=medicine_id,
            delta=-med.quantity,
            reason="Expired Write-Off",
            reference_note=f"Expired on {med.expiry_date}",
        )

    def delete_medicine(self, medicine_id: int) -> None:
        """Delete a medicine if it has no historical sales references."""
        existing = self.get_medicine(medicine_id)
        if not existing:
            raise ValidationError(f"Medicine #{medicine_id} was not found.")

        sales_ref_count = self.db.connection.execute(
            "SELECT COUNT(*) FROM sale_items WHERE medicine_id = ?",
            (medicine_id,),
        ).fetchone()[0]
        if sales_ref_count > 0:
            raise BusinessRuleError(
                f"Cannot delete '{existing.name}' because it appears on {sales_ref_count} "
                "historical sale line(s). Set stock to 0 instead to retire this batch."
            )

        with self.db.transaction() as conn:
            conn.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))

    def list_recent_adjustments(self, limit: int = 50) -> list[StockAdjustment]:
        """Return recent stock adjustment audit log entries."""
        rows = self.db.connection.execute(
            """
            SELECT sa.*, m.name AS medicine_name
            FROM stock_adjustments sa
            JOIN medicines m ON m.id = sa.medicine_id
            ORDER BY sa.id DESC
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()
        return [
            StockAdjustment(
                id=row["id"],
                medicine_id=row["medicine_id"],
                change_qty=int(row["change_qty"]),
                reason=row["reason"],
                reference_note=row["reference_note"],
                created_at=row["created_at"],
                medicine_name=row["medicine_name"],
            )
            for row in rows
        ]
