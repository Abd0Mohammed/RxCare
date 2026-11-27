"""Supplier CRUD and validation service."""

from __future__ import annotations

import sqlite3

from pharmacy.database.db_manager import DatabaseManager
from pharmacy.models.entities import Supplier
from pharmacy.utils import (
    BusinessRuleError,
    ValidationError,
    now_timestamp,
    validate_non_empty,
    validate_optional_email,
)


class SupplierService:
    """Handles supplier creation, updates, queries, and deletion safeguards."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    @staticmethod
    def _row_to_supplier(row: sqlite3.Row) -> Supplier:
        return Supplier(
            id=row["id"],
            name=row["name"],
            contact_person=row["contact_person"],
            phone=row["phone"],
            email=row["email"],
            address=row["address"],
            created_at=row["created_at"],
            medicine_count=row["medicine_count"] if "medicine_count" in row.keys() else 0,
        )

    def list_suppliers(self, search_query: str = "") -> list[Supplier]:
        """Return all suppliers (optionally filtered by name, contact, or phone)."""
        query = f"%{(search_query or '').strip()}%"
        sql = """
            SELECT s.*, COUNT(m.id) AS medicine_count
            FROM suppliers s
            LEFT JOIN medicines m ON m.supplier_id = s.id
            WHERE s.name LIKE ? OR s.contact_person LIKE ? OR s.phone LIKE ? OR s.email LIKE ?
            GROUP BY s.id
            ORDER BY s.name COLLATE NOCASE ASC
        """
        rows = self.db.connection.execute(sql, (query, query, query, query)).fetchall()
        return [self._row_to_supplier(row) for row in rows]

    def get_supplier(self, supplier_id: int) -> Supplier | None:
        """Fetch a single supplier by primary key."""
        row = self.db.connection.execute(
            """
            SELECT s.*, COUNT(m.id) AS medicine_count
            FROM suppliers s
            LEFT JOIN medicines m ON m.supplier_id = s.id
            WHERE s.id = ?
            GROUP BY s.id
            """,
            (supplier_id,),
        ).fetchone()
        return self._row_to_supplier(row) if row else None

    def create_supplier(
        self,
        name: str,
        contact_person: str = "",
        phone: str = "",
        email: str = "",
        address: str = "",
    ) -> Supplier:
        """Validate and insert a new supplier."""
        clean_name = validate_non_empty(name, "Supplier name")
        clean_email = validate_optional_email(email)
        created_at = now_timestamp()

        try:
            with self.db.transaction() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO suppliers (name, contact_person, phone, email, address, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        clean_name,
                        (contact_person or "").strip(),
                        (phone or "").strip(),
                        clean_email,
                        (address or "").strip(),
                        created_at,
                    ),
                )
                supplier_id = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError(
                f"A supplier named '{clean_name}' already exists."
            ) from exc

        created = self.get_supplier(int(supplier_id))
        assert created is not None
        return created

    def update_supplier(
        self,
        supplier_id: int,
        name: str,
        contact_person: str = "",
        phone: str = "",
        email: str = "",
        address: str = "",
    ) -> Supplier:
        """Validate and update an existing supplier."""
        existing = self.get_supplier(supplier_id)
        if not existing:
            raise ValidationError(f"Supplier #{supplier_id} was not found.")

        clean_name = validate_non_empty(name, "Supplier name")
        clean_email = validate_optional_email(email)

        try:
            with self.db.transaction() as conn:
                conn.execute(
                    """
                    UPDATE suppliers
                    SET name = ?, contact_person = ?, phone = ?, email = ?, address = ?
                    WHERE id = ?
                    """,
                    (
                        clean_name,
                        (contact_person or "").strip(),
                        (phone or "").strip(),
                        clean_email,
                        (address or "").strip(),
                        supplier_id,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValidationError(
                f"Another supplier named '{clean_name}' already exists."
            ) from exc

        updated = self.get_supplier(supplier_id)
        assert updated is not None
        return updated

    def delete_supplier(self, supplier_id: int) -> None:
        """Delete a supplier if no medicines currently reference it."""
        existing = self.get_supplier(supplier_id)
        if not existing:
            raise ValidationError(f"Supplier #{supplier_id} was not found.")

        if existing.medicine_count > 0:
            raise BusinessRuleError(
                f"Cannot delete '{existing.name}' because {existing.medicine_count} "
                "medicine record(s) are assigned to this supplier."
            )

        with self.db.transaction() as conn:
            conn.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
