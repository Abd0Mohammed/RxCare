"""Dashboard KPI aggregation, sales analytics, and CSV reporting service."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from pharmacy.config import DEFAULT_EXPIRY_WARNING_DAYS
from pharmacy.database.db_manager import DatabaseManager
from pharmacy.models.entities import DashboardStats
from pharmacy.utils import export_rows_to_csv, parse_iso_date, today_date


class ReportService:
    """Computes live dashboard statistics, sales summaries, and CSV exports."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def get_dashboard_stats(
        self, warning_days: int = DEFAULT_EXPIRY_WARNING_DAYS
    ) -> DashboardStats:
        """Compute current inventory, expiry, supplier, and revenue metrics."""
        conn = self.db.connection
        today = today_date()
        today_str = today.isoformat()
        warn_str = (today + timedelta(days=max(1, int(warning_days)))).isoformat()

        inv_row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_medicines,
                COALESCE(SUM(quantity), 0) AS total_stock_units,
                COALESCE(SUM(quantity * unit_price), 0.0) AS retail_value,
                COALESCE(SUM(quantity * cost_price), 0.0) AS cost_value,
                COALESCE(SUM(CASE WHEN quantity <= reorder_level THEN 1 ELSE 0 END), 0) AS low_stock_count,
                COALESCE(SUM(CASE WHEN expiry_date > ? AND expiry_date <= ? THEN 1 ELSE 0 END), 0) AS expiring_soon_count,
                COALESCE(SUM(CASE WHEN expiry_date <= ? THEN 1 ELSE 0 END), 0) AS expired_count
            FROM medicines
            """,
            (today_str, warn_str, today_str),
        ).fetchone()

        supplier_count = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]

        today_sales_row = conn.execute(
            """
            SELECT
                COUNT(*) AS cnt,
                COALESCE(SUM(total_amount), 0.0) AS revenue
            FROM sales
            WHERE substr(sale_date, 1, 10) = ?
            """,
            (today_str,),
        ).fetchone()

        total_sales_row = conn.execute(
            """
            SELECT
                COUNT(*) AS cnt,
                COALESCE(SUM(total_amount), 0.0) AS revenue
            FROM sales
            """
        ).fetchone()

        return DashboardStats(
            total_medicines=int(inv_row["total_medicines"]),
            total_stock_units=int(inv_row["total_stock_units"]),
            inventory_retail_value=round(float(inv_row["retail_value"]), 2),
            inventory_cost_value=round(float(inv_row["cost_value"]), 2),
            low_stock_count=int(inv_row["low_stock_count"]),
            expiring_soon_count=int(inv_row["expiring_soon_count"]),
            expired_count=int(inv_row["expired_count"]),
            total_suppliers=int(supplier_count),
            today_sales_count=int(today_sales_row["cnt"]),
            today_revenue=round(float(today_sales_row["revenue"]), 2),
            total_sales_count=int(total_sales_row["cnt"]),
            total_revenue=round(float(total_sales_row["revenue"]), 2),
        )

    def get_sales_summary_by_range(
        self, start_date: str, end_date: str
    ) -> dict[str, float | int]:
        """Return aggregated sales count, subtotal, discount, tax, and net revenue."""
        start = parse_iso_date(start_date, "Start date").isoformat()
        end = parse_iso_date(end_date, "End date").isoformat()
        row = self.db.connection.execute(
            """
            SELECT
                COUNT(*) AS invoice_count,
                COALESCE(SUM(subtotal), 0.0) AS gross_subtotal,
                COALESCE(SUM(discount_amount), 0.0) AS total_discount,
                COALESCE(SUM(tax_amount), 0.0) AS total_tax,
                COALESCE(SUM(total_amount), 0.0) AS net_revenue
            FROM sales
            WHERE substr(sale_date, 1, 10) BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()
        return {
            "invoice_count": int(row["invoice_count"]),
            "gross_subtotal": round(float(row["gross_subtotal"]), 2),
            "total_discount": round(float(row["total_discount"]), 2),
            "total_tax": round(float(row["total_tax"]), 2),
            "net_revenue": round(float(row["net_revenue"]), 2),
        }

    def get_top_selling_medicines(
        self, start_date: str | None = None, end_date: str | None = None, limit: int = 15
    ) -> list[dict[str, object]]:
        """Return top medicines ranked by units sold and revenue."""
        clauses = ["1=1"]
        params: list[object] = []
        if start_date:
            clauses.append("substr(s.sale_date, 1, 10) >= ?")
            params.append(parse_iso_date(start_date, "Start date").isoformat())
        if end_date:
            clauses.append("substr(s.sale_date, 1, 10) <= ?")
            params.append(parse_iso_date(end_date, "End date").isoformat())
        params.append(max(1, int(limit)))

        rows = self.db.connection.execute(
            f"""
            SELECT
                si.medicine_name,
                si.batch_number,
                SUM(si.quantity) AS units_sold,
                ROUND(SUM(si.line_total), 2) AS total_revenue
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE {' AND '.join(clauses)}
            GROUP BY si.medicine_id, si.medicine_name, si.batch_number
            ORDER BY units_sold DESC, total_revenue DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [
            {
                "medicine_name": row["medicine_name"],
                "batch_number": row["batch_number"],
                "units_sold": int(row["units_sold"]),
                "total_revenue": round(float(row["total_revenue"]), 2),
            }
            for row in rows
        ]

    def get_category_inventory_breakdown(self) -> list[dict[str, object]]:
        """Return medicine counts, stock units, and retail value grouped by category."""
        rows = self.db.connection.execute(
            """
            SELECT
                category,
                COUNT(*) AS sku_count,
                COALESCE(SUM(quantity), 0) AS total_units,
                ROUND(COALESCE(SUM(quantity * unit_price), 0.0), 2) AS retail_value
            FROM medicines
            GROUP BY category
            ORDER BY retail_value DESC, category ASC
            """
        ).fetchall()
        return [
            {
                "category": row["category"],
                "sku_count": int(row["sku_count"]),
                "total_units": int(row["total_units"]),
                "retail_value": round(float(row["retail_value"]), 2),
            }
            for row in rows
        ]

    def export_sales_csv(
        self, file_path: str | Path, start_date: str | None = None, end_date: str | None = None
    ) -> int:
        """Export sales invoices to CSV."""
        clauses = ["1=1"]
        params: list[object] = []
        if start_date:
            clauses.append("substr(sale_date, 1, 10) >= ?")
            params.append(parse_iso_date(start_date, "Start date").isoformat())
        if end_date:
            clauses.append("substr(sale_date, 1, 10) <= ?")
            params.append(parse_iso_date(end_date, "End date").isoformat())

        rows = self.db.connection.execute(
            f"""
            SELECT
                invoice_number, sale_date, customer_name, customer_phone,
                payment_method, subtotal, discount_amount, tax_amount,
                total_amount, amount_paid, change_due
            FROM sales
            WHERE {' AND '.join(clauses)}
            ORDER BY id DESC
            """,
            params,
        ).fetchall()

        headers = [
            "Invoice Number",
            "Sale Date",
            "Customer Name",
            "Customer Phone",
            "Payment Method",
            "Subtotal",
            "Discount",
            "Tax",
            "Grand Total",
            "Amount Paid",
            "Change Due",
        ]
        data = [tuple(row[col] for col in row.keys()) for row in rows]
        return export_rows_to_csv(file_path, headers, data)

    def export_inventory_csv(self, file_path: str | Path) -> int:
        """Export current medicine inventory to CSV."""
        rows = self.db.connection.execute(
            """
            SELECT
                m.id, m.name, m.generic_name, m.category, m.batch_number,
                COALESCE(s.name, 'Unassigned') AS supplier_name,
                m.cost_price, m.unit_price, m.quantity, m.reorder_level, m.expiry_date
            FROM medicines m
            LEFT JOIN suppliers s ON s.id = m.supplier_id
            ORDER BY m.name COLLATE NOCASE ASC
            """
        ).fetchall()
        headers = [
            "ID",
            "Medicine Name",
            "Generic Name",
            "Category",
            "Batch Number",
            "Supplier",
            "Cost Price",
            "Unit Price",
            "Quantity",
            "Reorder Level",
            "Expiry Date",
        ]
        data = [tuple(row[col] for col in row.keys()) for row in rows]
        return export_rows_to_csv(file_path, headers, data)
