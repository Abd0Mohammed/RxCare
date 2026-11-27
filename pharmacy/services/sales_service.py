"""Point-of-Sale (POS) billing, expiry enforcement, and atomic sales transactions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from pharmacy.database.db_manager import DatabaseManager
from pharmacy.models.entities import CartItem, Sale, SaleItem
from pharmacy.utils import (
    BusinessRuleError,
    ValidationError,
    is_expired,
    now_timestamp,
    parse_non_negative_float,
    parse_positive_int,
    today_date,
)


@dataclass(frozen=True)
class SaleCalculation:
    subtotal: float
    discount_percent: float
    discount_amount: float
    tax_percent: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    change_due: float


class SalesService:
    """Handles POS calculations, expiry validation, and atomic checkout."""

    VALID_PAYMENT_METHODS = ("Cash", "Card", "Insurance / Digital")

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    @staticmethod
    def calculate_totals(
        items: list[CartItem],
        discount_percent: object = 0.0,
        tax_percent: object = 0.0,
        amount_paid: object | None = None,
        payment_method: str = "Cash",
    ) -> SaleCalculation:
        """Compute exact subtotal, discount, tax, grand total, and change due."""
        disc_pct = parse_non_negative_float(discount_percent, "Discount %")
        if disc_pct > 100.0:
            raise ValidationError("Discount percentage cannot exceed 100%.")

        tax_pct = parse_non_negative_float(tax_percent, "Tax %")
        if tax_pct > 100.0:
            raise ValidationError("Tax percentage cannot exceed 100%.")

        subtotal = round(sum(round(item.unit_price * item.quantity, 2) for item in items), 2)
        discount_amount = round(subtotal * (disc_pct / 100.0), 2)
        taxable_amount = max(0.0, round(subtotal - discount_amount, 2))
        tax_amount = round(taxable_amount * (tax_pct / 100.0), 2)
        total_amount = round(taxable_amount + tax_amount, 2)

        if amount_paid is None or str(amount_paid).strip() == "":
            paid = total_amount
        else:
            paid = parse_non_negative_float(amount_paid, "Amount paid")
            if paid < total_amount:
                raise ValidationError(
                    f"Amount paid ({paid:.2f}) is less than grand total ({total_amount:.2f})."
                )

        if payment_method != "Cash" and amount_paid is None:
            paid = total_amount

        change_due = max(0.0, round(paid - total_amount, 2))
        return SaleCalculation(
            subtotal=subtotal,
            discount_percent=disc_pct,
            discount_amount=discount_amount,
            tax_percent=tax_pct,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=paid,
            change_due=change_due,
        )

    def validate_medicine_for_cart(
        self, medicine_id: int, requested_qty: int
    ) -> tuple[int, str, str, float, int, str]:
        """Validate stock and expiry for adding a medicine to the POS cart."""
        qty = parse_positive_int(requested_qty, "Quantity")
        row = self.db.connection.execute(
            """
            SELECT id, name, batch_number, unit_price, quantity, expiry_date
            FROM medicines
            WHERE id = ?
            """,
            (medicine_id,),
        ).fetchone()
        if not row:
            raise ValidationError(f"Medicine #{medicine_id} was not found.")

        if is_expired(row["expiry_date"]):
            raise BusinessRuleError(
                f"Sale blocked: '{row['name']}' (Batch {row['batch_number']}) "
                f"expired on {row['expiry_date']}."
            )

        available = int(row["quantity"])
        if available <= 0:
            raise BusinessRuleError(
                f"'{row['name']}' (Batch {row['batch_number']}) is out of stock."
            )
        if qty > available:
            raise BusinessRuleError(
                f"Insufficient stock for '{row['name']}': requested {qty}, available {available}."
            )

        return (
            int(row["id"]),
            str(row["name"]),
            str(row["batch_number"]),
            float(row["unit_price"]),
            available,
            str(row["expiry_date"]),
        )

    def create_sale(
        self,
        cart_items: list[CartItem],
        customer_name: str = "Walk-in Customer",
        customer_phone: str = "",
        discount_percent: object = 0.0,
        tax_percent: object = 0.0,
        amount_paid: object | None = None,
        payment_method: str = "Cash",
        notes: str = "",
    ) -> Sale:
        """Execute an atomic POS sale transaction.

        Validates every item against live DB stock and expiry inside BEGIN IMMEDIATE.
        If any line fails, the entire transaction rolls back cleanly.
        """
        if not cart_items:
            raise ValidationError("Cannot complete checkout with an empty cart.")

        clean_method = (payment_method or "Cash").strip()
        if clean_method not in self.VALID_PAYMENT_METHODS:
            raise ValidationError(f"Unsupported payment method '{clean_method}'.")

        clean_customer = (customer_name or "").strip() or "Walk-in Customer"
        clean_phone = (customer_phone or "").strip()
        clean_notes = (notes or "").strip()
        sale_ts = now_timestamp()
        today_stamp = today_date().strftime("%Y%m%d")

        # Consolidate duplicate medicine_ids if passed programmatically
        consolidated: dict[int, int] = {}
        for item in cart_items:
            qty = parse_positive_int(item.quantity, f"Quantity for {item.medicine_name}")
            consolidated[item.medicine_id] = consolidated.get(item.medicine_id, 0) + qty

        with self.db.transaction() as conn:
            verified_items: list[CartItem] = []

            for med_id, total_qty in consolidated.items():
                row = conn.execute(
                    """
                    SELECT id, name, batch_number, unit_price, quantity, expiry_date
                    FROM medicines
                    WHERE id = ?
                    """,
                    (med_id,),
                ).fetchone()
                if not row:
                    raise ValidationError(f"Medicine #{med_id} no longer exists.")

                if is_expired(row["expiry_date"]):
                    raise BusinessRuleError(
                        f"Sale blocked: '{row['name']}' (Batch {row['batch_number']}) "
                        f"expired on {row['expiry_date']}."
                    )

                available = int(row["quantity"])
                if total_qty > available:
                    raise BusinessRuleError(
                        f"Insufficient stock for '{row['name']}': requested {total_qty}, "
                        f"available {available}."
                    )

                verified_items.append(
                    CartItem(
                        medicine_id=int(row["id"]),
                        medicine_name=str(row["name"]),
                        batch_number=str(row["batch_number"]),
                        unit_price=float(row["unit_price"]),
                        quantity=total_qty,
                        available_stock=available,
                        expiry_date=str(row["expiry_date"]),
                    )
                )

            totals = self.calculate_totals(
                items=verified_items,
                discount_percent=discount_percent,
                tax_percent=tax_percent,
                amount_paid=amount_paid,
                payment_method=clean_method,
            )

            next_seq = conn.execute(
                "SELECT COALESCE(MAX(id), 0) + 1 FROM sales"
            ).fetchone()[0]
            invoice_number = f"INV-{today_stamp}-{int(next_seq):04d}"

            sale_cur = conn.execute(
                """
                INSERT INTO sales (
                    invoice_number, customer_name, customer_phone,
                    subtotal, discount_percent, discount_amount,
                    tax_percent, tax_amount, total_amount,
                    amount_paid, change_due, payment_method, sale_date, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_number,
                    clean_customer,
                    clean_phone,
                    totals.subtotal,
                    totals.discount_percent,
                    totals.discount_amount,
                    totals.tax_percent,
                    totals.tax_amount,
                    totals.total_amount,
                    totals.amount_paid,
                    totals.change_due,
                    clean_method,
                    sale_ts,
                    clean_notes,
                ),
            )
            sale_id = int(sale_cur.lastrowid)

            for item in verified_items:
                conn.execute(
                    """
                    INSERT INTO sale_items (
                        sale_id, medicine_id, medicine_name, batch_number,
                        quantity, unit_price, line_total
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sale_id,
                        item.medicine_id,
                        item.medicine_name,
                        item.batch_number,
                        item.quantity,
                        item.unit_price,
                        item.line_total,
                    ),
                )
                conn.execute(
                    "UPDATE medicines SET quantity = quantity - ?, updated_at = ? WHERE id = ?",
                    (item.quantity, sale_ts, item.medicine_id),
                )
                conn.execute(
                    """
                    INSERT INTO stock_adjustments (
                        medicine_id, change_qty, reason, reference_note, created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item.medicine_id,
                        -item.quantity,
                        "Sale",
                        invoice_number,
                        sale_ts,
                    ),
                )

        created = self.get_sale(sale_id)
        assert created is not None
        return created

    def get_sale(self, sale_id: int) -> Sale | None:
        """Fetch a sale header and all associated line items."""
        row = self.db.connection.execute(
            "SELECT * FROM sales WHERE id = ?", (sale_id,)
        ).fetchone()
        if not row:
            return None

        item_rows = self.db.connection.execute(
            "SELECT * FROM sale_items WHERE sale_id = ? ORDER BY id ASC", (sale_id,)
        ).fetchall()
        items = [
            SaleItem(
                id=ir["id"],
                sale_id=ir["sale_id"],
                medicine_id=ir["medicine_id"],
                medicine_name=ir["medicine_name"],
                batch_number=ir["batch_number"],
                quantity=int(ir["quantity"]),
                unit_price=float(ir["unit_price"]),
                line_total=float(ir["line_total"]),
            )
            for ir in item_rows
        ]
        return self._row_to_sale(row, items)

    @staticmethod
    def _row_to_sale(row: sqlite3.Row, items: list[SaleItem] | None = None) -> Sale:
        return Sale(
            id=row["id"],
            invoice_number=row["invoice_number"],
            customer_name=row["customer_name"],
            customer_phone=row["customer_phone"],
            subtotal=float(row["subtotal"]),
            discount_percent=float(row["discount_percent"]),
            discount_amount=float(row["discount_amount"]),
            tax_percent=float(row["tax_percent"]),
            tax_amount=float(row["tax_amount"]),
            total_amount=float(row["total_amount"]),
            amount_paid=float(row["amount_paid"]),
            change_due=float(row["change_due"]),
            payment_method=row["payment_method"],
            sale_date=row["sale_date"],
            notes=row["notes"],
            items=items or [],
        )

    def list_sales(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        search_query: str = "",
        limit: int = 200,
    ) -> list[Sale]:
        """Return sales headers filtered by optional date range and search string."""
        clauses = ["1=1"]
        params: list[object] = []

        if start_date:
            clauses.append("substr(sale_date, 1, 10) >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("substr(sale_date, 1, 10) <= ?")
            params.append(end_date)
        if (search_query or "").strip():
            q = f"%{search_query.strip()}%"
            clauses.append("(invoice_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)")
            params.extend([q, q, q])

        params.append(max(1, int(limit)))
        sql = f"""
            SELECT * FROM sales
            WHERE {' AND '.join(clauses)}
            ORDER BY id DESC
            LIMIT ?
        """
        rows = self.db.connection.execute(sql, params).fetchall()
        return [self._row_to_sale(row) for row in rows]
