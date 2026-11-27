"""SQLite3 connection lifecycle, schema initialization, transactions, and seeding."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Iterator

from pharmacy.config import DEFAULT_DB_PATH
from pharmacy.utils import now_timestamp, today_date


class DatabaseManager:
    """Manages SQLite3 connection, schema setup, and atomic transactions."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path: str | Path = db_path if db_path is not None else DEFAULT_DB_PATH
        if str(self.db_path) != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # isolation_level=None enables explicit BEGIN IMMEDIATE / COMMIT / ROLLBACK.
        self._conn = sqlite3.connect(str(self.db_path), isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.execute("PRAGMA busy_timeout = 5000;")
        self._tx_depth = 0
        self._closed = False

        self.initialize_schema()

    @property
    def connection(self) -> sqlite3.Connection:
        """Return active SQLite connection, raising if already closed."""
        if self._closed:
            raise RuntimeError("Database connection is closed.")
        return self._conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Provide an atomic transaction context with savepoint nesting support."""
        conn = self.connection
        is_outer = self._tx_depth == 0
        savepoint_name = f"sp_{self._tx_depth}"

        if is_outer:
            conn.execute("BEGIN IMMEDIATE;")
        else:
            conn.execute(f"SAVEPOINT {savepoint_name};")

        self._tx_depth += 1
        try:
            yield conn
        except Exception:
            if is_outer:
                if conn.in_transaction:
                    conn.execute("ROLLBACK;")
            else:
                conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
                conn.execute(f"RELEASE SAVEPOINT {savepoint_name};")
            raise
        else:
            if is_outer:
                if conn.in_transaction:
                    conn.execute("COMMIT;")
            else:
                conn.execute(f"RELEASE SAVEPOINT {savepoint_name};")
        finally:
            self._tx_depth -= 1

    def initialize_schema(self) -> None:
        """Create required tables and indexes if they do not exist."""
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                contact_person TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                generic_name TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'General',
                batch_number TEXT NOT NULL UNIQUE,
                supplier_id INTEGER REFERENCES suppliers(id) ON DELETE RESTRICT,
                cost_price REAL NOT NULL CHECK (cost_price >= 0),
                unit_price REAL NOT NULL CHECK (unit_price > 0),
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                reorder_level INTEGER NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
                expiry_date TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL UNIQUE,
                customer_name TEXT NOT NULL DEFAULT 'Walk-in Customer',
                customer_phone TEXT NOT NULL DEFAULT '',
                subtotal REAL NOT NULL CHECK (subtotal >= 0),
                discount_percent REAL NOT NULL DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
                discount_amount REAL NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
                tax_percent REAL NOT NULL DEFAULT 0 CHECK (tax_percent >= 0 AND tax_percent <= 100),
                tax_amount REAL NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
                total_amount REAL NOT NULL CHECK (total_amount >= 0),
                amount_paid REAL NOT NULL CHECK (amount_paid >= 0),
                change_due REAL NOT NULL DEFAULT 0 CHECK (change_due >= 0),
                payment_method TEXT NOT NULL DEFAULT 'Cash',
                sale_date TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE RESTRICT,
                medicine_name TEXT NOT NULL,
                batch_number TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price > 0),
                line_total REAL NOT NULL CHECK (line_total >= 0)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS stock_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
                change_qty INTEGER NOT NULL,
                reason TEXT NOT NULL,
                reference_note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """,
            "CREATE INDEX IF NOT EXISTS idx_medicines_name ON medicines(name);",
            "CREATE INDEX IF NOT EXISTS idx_medicines_expiry ON medicines(expiry_date);",
            "CREATE INDEX IF NOT EXISTS idx_medicines_supplier ON medicines(supplier_id);",
            "CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_medicine ON sale_items(medicine_id);",
        ]
        with self.transaction() as conn:
            for stmt in ddl_statements:
                conn.execute(stmt)

    def is_empty(self) -> bool:
        """Return True if core catalog tables have no rows."""
        cur = self.connection.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = cur.fetchone()[0]
        cur = self.connection.execute("SELECT COUNT(*) FROM medicines")
        medicines_count = cur.fetchone()[0]
        return suppliers_count == 0 and medicines_count == 0

    def seed_sample_data(self) -> bool:
        """Populate initial demonstration records if the database is empty."""
        if not self.is_empty():
            return False

        now = now_timestamp()
        today = today_date()

        with self.transaction() as conn:
            suppliers = [
                (
                    "MedLine Pharma Distributors",
                    "Sarah Jenkins",
                    "+1-555-0101",
                    "orders@medlinepharma.example",
                    "420 Commerce Way, Suite 200",
                    now,
                ),
                (
                    "Apex BioHealth Supply",
                    "Marcus Vance",
                    "+1-555-0148",
                    "supply@apexbio.example",
                    "88 Harbor Industrial Park",
                    now,
                ),
                (
                    "CareWell Generics Corp",
                    "Priya Nair",
                    "+1-555-0192",
                    "sales@carewell.example",
                    "1500 Meridian Blvd",
                    now,
                ),
            ]
            conn.executemany(
                """
                INSERT INTO suppliers (name, contact_person, phone, email, address, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                suppliers,
            )

            supplier_rows = conn.execute(
                "SELECT id, name FROM suppliers ORDER BY id"
            ).fetchall()
            s1, s2, s3 = supplier_rows[0]["id"], supplier_rows[1]["id"], supplier_rows[2]["id"]

            medicines = [
                (
                    "Amoxicillin 500mg Capsules",
                    "Amoxicillin",
                    "Antibiotics",
                    "AMX-2026-01",
                    s1,
                    8.50,
                    14.50,
                    85,
                    20,
                    (today + timedelta(days=365)).isoformat(),
                    "Broad-spectrum penicillin antibiotic (pack of 20)",
                    now,
                    now,
                ),
                (
                    "Paracetamol 500mg Tablets",
                    "Acetaminophen",
                    "Analgesics",
                    "PCM-2026-14",
                    s3,
                    2.20,
                    5.00,
                    140,
                    30,
                    (today + timedelta(days=420)).isoformat(),
                    "Pain reliever and fever reducer (pack of 24)",
                    now,
                    now,
                ),
                (
                    "Lisinopril 10mg Tablets",
                    "Lisinopril",
                    "Cardiovascular",
                    "LSN-2026-07",
                    s2,
                    6.00,
                    12.00,
                    8,
                    15,
                    (today + timedelta(days=210)).isoformat(),
                    "ACE inhibitor for hypertension (bottle of 30)",
                    now,
                    now,
                ),
                (
                    "Metformin 850mg ER",
                    "Metformin Hydrochloride",
                    "Endocrinology",
                    "MTF-2026-03",
                    s3,
                    5.40,
                    11.25,
                    45,
                    15,
                    (today + timedelta(days=18)).isoformat(),
                    "Extended-release blood glucose control (pack of 30)",
                    now,
                    now,
                ),
                (
                    "Azithromycin 250mg Pack",
                    "Azithromycin",
                    "Antibiotics",
                    "AZM-2025-09",
                    s1,
                    9.80,
                    18.00,
                    12,
                    10,
                    (today - timedelta(days=14)).isoformat(),
                    "Macrolide antibiotic (expired sample batch for quarantine demo)",
                    now,
                    now,
                ),
                (
                    "Omeprazole 20mg Delayed-Release",
                    "Omeprazole",
                    "Gastrointestinal",
                    "OMP-2026-22",
                    s2,
                    4.75,
                    9.90,
                    60,
                    15,
                    (today + timedelta(days=290)).isoformat(),
                    "Proton pump inhibitor for acid reflux (pack of 28)",
                    now,
                    now,
                ),
                (
                    "Cetirizine 10mg Allergy Relief",
                    "Cetirizine Hydrochloride",
                    "Antihistamines",
                    "CTZ-2026-11",
                    s3,
                    3.10,
                    7.50,
                    6,
                    12,
                    (today + timedelta(days=150)).isoformat(),
                    "Non-drowsy 24-hour antihistamine (pack of 30)",
                    now,
                    now,
                ),
            ]
            conn.executemany(
                """
                INSERT INTO medicines (
                    name, generic_name, category, batch_number, supplier_id,
                    cost_price, unit_price, quantity, reorder_level, expiry_date,
                    description, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                medicines,
            )

            med_rows = conn.execute(
                "SELECT id, name, batch_number, unit_price FROM medicines ORDER BY id"
            ).fetchall()
            m1, m2 = med_rows[0], med_rows[1]

            # Record one completed historical sale from today for realistic dashboard KPIs
            subtotal = round(m1["unit_price"] * 2 + m2["unit_price"] * 3, 2)
            tax_pct = 5.0
            tax_amt = round(subtotal * (tax_pct / 100.0), 2)
            total = round(subtotal + tax_amt, 2)

            cur = conn.execute(
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
                    f"INV-{today.strftime('%Y%m%d')}-0001",
                    "Eleanor Vance",
                    "+1-555-0177",
                    subtotal,
                    0.0,
                    0.0,
                    tax_pct,
                    tax_amt,
                    total,
                    50.00,
                    round(50.00 - total, 2),
                    "Cash",
                    now,
                    "Sample initial transaction",
                ),
            )
            sale_id = cur.lastrowid

            conn.executemany(
                """
                INSERT INTO sale_items (
                    sale_id, medicine_id, medicine_name, batch_number,
                    quantity, unit_price, line_total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        sale_id,
                        m1["id"],
                        m1["name"],
                        m1["batch_number"],
                        2,
                        m1["unit_price"],
                        round(m1["unit_price"] * 2, 2),
                    ),
                    (
                        sale_id,
                        m2["id"],
                        m2["name"],
                        m2["batch_number"],
                        3,
                        m2["unit_price"],
                        round(m2["unit_price"] * 3, 2),
                    ),
                ],
            )
        return True

    def close(self) -> None:
        """Close the SQLite connection cleanly on shutdown."""
        if not self._closed:
            self._conn.close()
            self._closed = True
