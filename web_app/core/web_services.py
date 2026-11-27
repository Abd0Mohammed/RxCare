"""Web-specific analytics, cart/idempotency management, and service container."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, MutableMapping

from pharmacy.config import DEFAULT_EXPIRY_WARNING_DAYS
from pharmacy.models.entities import CartItem, Medicine, Sale
from pharmacy.services.inventory_service import InventoryService
from pharmacy.services.report_service import ReportService
from pharmacy.services.sales_service import SaleCalculation, SalesService
from pharmacy.services.supplier_service import SupplierService
from pharmacy.utils import ValidationError, parse_iso_date, parse_non_negative_float, today_date
from web_app.core.db_adapter import WebSQLiteDatabaseManager, create_database_backend
from web_app.core.i18n import DEFAULT_LANG, NAV_PAGE_KEYS, SUPPORTED_LANGS


@dataclass(frozen=True)
class ProfitSummary:
    gross_revenue: float
    gross_cost: float
    total_discount: float
    gross_profit: float
    net_profit: float
    transaction_count: int


class WebAnalyticsService:
    """Provides web-specific profit, daily trend, and category queries on top of desktop DB."""

    def __init__(self, db: WebSQLiteDatabaseManager) -> None:
        self.db = db

    def get_profit_summary(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> ProfitSummary:
        """Compute revenue, COGS, discounts, and net profit over an optional date range."""
        clauses = ["1=1"]
        params: list[object] = []
        if start_date:
            clauses.append("substr(s.sale_date, 1, 10) >= ?")
            params.append(parse_iso_date(start_date, "Start date").isoformat())
        if end_date:
            clauses.append("substr(s.sale_date, 1, 10) <= ?")
            params.append(parse_iso_date(end_date, "End date").isoformat())

        where_sql = " AND ".join(clauses)

        sales_row = self.db.connection.execute(
            f"""
            SELECT
                COUNT(*) AS tx_count,
                COALESCE(SUM(s.subtotal), 0.0) AS gross_subtotal,
                COALESCE(SUM(s.discount_amount), 0.0) AS total_discount,
                COALESCE(SUM(s.total_amount), 0.0) AS net_revenue
            FROM sales s
            WHERE {where_sql}
            """,
            params,
        ).fetchone()

        cogs_row = self.db.connection.execute(
            f"""
            SELECT
                COALESCE(SUM(si.quantity * COALESCE(m.cost_price, 0.0)), 0.0) AS total_cost,
                COALESCE(SUM(si.line_total), 0.0) AS item_revenue
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            LEFT JOIN medicines m ON m.id = si.medicine_id
            WHERE {where_sql}
            """,
            params,
        ).fetchone()

        gross_revenue = round(float(sales_row["net_revenue"]), 2)
        gross_cost = round(float(cogs_row["total_cost"]), 2)
        total_discount = round(float(sales_row["total_discount"]), 2)
        item_revenue = round(float(cogs_row["item_revenue"]), 2)
        gross_profit = round(item_revenue - gross_cost, 2)
        net_profit = round(gross_profit - total_discount, 2)

        return ProfitSummary(
            gross_revenue=gross_revenue,
            gross_cost=gross_cost,
            total_discount=total_discount,
            gross_profit=gross_profit,
            net_profit=net_profit,
            transaction_count=int(sales_row["tx_count"]),
        )

    def calculate_cart_profit(
        self, items: list[CartItem], discount_percent: object = 0.0
    ) -> dict[str, float]:
        """Compute estimated cost, gross profit, and net profit for the active POS cart."""
        disc_pct = parse_non_negative_float(discount_percent, "Discount %")
        if disc_pct > 100.0:
            raise ValidationError("Discount percentage cannot exceed 100%.")

        if not items:
            return {"cost": 0.0, "gross_profit": 0.0, "net_profit": 0.0}

        med_ids = [item.medicine_id for item in items]
        placeholders = ",".join("?" for _ in med_ids)
        rows = self.db.connection.execute(
            f"SELECT id, cost_price FROM medicines WHERE id IN ({placeholders})",
            med_ids,
        ).fetchall()
        cost_map = {int(r["id"]): float(r["cost_price"]) for r in rows}

        subtotal = round(sum(item.line_total for item in items), 2)
        total_cost = round(
            sum(cost_map.get(item.medicine_id, 0.0) * item.quantity for item in items), 2
        )
        discount_amount = round(subtotal * (disc_pct / 100.0), 2)
        gross_profit = round(subtotal - total_cost, 2)
        net_profit = round(gross_profit - discount_amount, 2)
        return {
            "cost": total_cost,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
        }

    def get_daily_sales_series(
        self, start_date: str, end_date: str
    ) -> list[dict[str, object]]:
        """Return per-day invoice counts, revenue, and estimated net profit."""
        start = parse_iso_date(start_date, "Start date").isoformat()
        end = parse_iso_date(end_date, "End date").isoformat()

        rows = self.db.connection.execute(
            """
            SELECT
                substr(s.sale_date, 1, 10) AS day,
                COUNT(DISTINCT s.id) AS invoice_count,
                ROUND(SUM(s.total_amount), 2) AS revenue,
                ROUND(SUM(s.discount_amount), 2) AS discount_total
            FROM sales s
            WHERE substr(s.sale_date, 1, 10) BETWEEN ? AND ?
            GROUP BY substr(s.sale_date, 1, 10)
            ORDER BY day ASC
            """,
            (start, end),
        ).fetchall()

        cost_rows = self.db.connection.execute(
            """
            SELECT
                substr(s.sale_date, 1, 10) AS day,
                ROUND(COALESCE(SUM(si.line_total - (si.quantity * COALESCE(m.cost_price, 0.0))), 0.0), 2) AS gross_profit
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            LEFT JOIN medicines m ON m.id = si.medicine_id
            WHERE substr(s.sale_date, 1, 10) BETWEEN ? AND ?
            GROUP BY substr(s.sale_date, 1, 10)
            """,
            (start, end),
        ).fetchall()
        gp_by_day = {r["day"]: float(r["gross_profit"]) for r in cost_rows}

        series: list[dict[str, object]] = []
        for row in rows:
            day = row["day"]
            discount = float(row["discount_total"] or 0.0)
            net_profit = round(gp_by_day.get(day, 0.0) - discount, 2)
            series.append(
                {
                    "date": day,
                    "invoice_count": int(row["invoice_count"]),
                    "revenue": round(float(row["revenue"] or 0.0), 2),
                    "profit": net_profit,
                }
            )
        return series

    def list_categories(self, inventory_service: InventoryService) -> list[str]:
        """Return sorted distinct categories currently in inventory."""
        cats = {
            (m.category or "General").strip()
            for m in inventory_service.list_medicines()
        }
        return sorted(cats, key=str.casefold)

    def filter_medicines(
        self,
        inventory_service: InventoryService,
        search_query: str = "",
        status_filter: str = "all",
        category: str = "All Categories",
        warning_days: int = DEFAULT_EXPIRY_WARNING_DAYS,
    ) -> list[Medicine]:
        """Reuse InventoryService search/status filters and apply category filter."""
        meds = inventory_service.list_medicines(
            search_query=search_query,
            status_filter=status_filter,
            warning_days=warning_days,
        )
        if category and category != "All Categories":
            meds = [m for m in meds if m.category == category]
        return meds


class WebSessionController:
    """Manages Streamlit-compatible session state for language, POS cart, and rerun idempotency."""

    CART_KEY = "rxcare_pos_cart"
    TOKEN_KEY = "rxcare_pos_tx_token"
    PROCESSED_TOKENS_KEY = "rxcare_processed_tx_tokens"
    LAST_SALE_KEY = "rxcare_last_completed_sale"
    FLASH_SUCCESS_KEY = "rxcare_flash_success"
    LANG_KEY = "rxcare_lang"
    PAGE_KEY = "rxcare_page_key"

    @classmethod
    def ensure_initialized(cls, session_state: MutableMapping[str, Any]) -> None:
        if cls.CART_KEY not in session_state:
            session_state[cls.CART_KEY] = {}
        if cls.TOKEN_KEY not in session_state:
            session_state[cls.TOKEN_KEY] = uuid.uuid4().hex
        if cls.PROCESSED_TOKENS_KEY not in session_state:
            session_state[cls.PROCESSED_TOKENS_KEY] = {}
        if cls.LAST_SALE_KEY not in session_state:
            session_state[cls.LAST_SALE_KEY] = None
        if cls.FLASH_SUCCESS_KEY not in session_state:
            session_state[cls.FLASH_SUCCESS_KEY] = None
        if cls.LANG_KEY not in session_state or session_state[cls.LANG_KEY] not in SUPPORTED_LANGS:
            session_state[cls.LANG_KEY] = DEFAULT_LANG
        if cls.PAGE_KEY not in session_state or session_state[cls.PAGE_KEY] not in NAV_PAGE_KEYS:
            session_state[cls.PAGE_KEY] = NAV_PAGE_KEYS[0]

    @classmethod
    def get_lang(cls, session_state: MutableMapping[str, Any]) -> str:
        cls.ensure_initialized(session_state)
        return str(session_state[cls.LANG_KEY])

    @classmethod
    def set_lang(cls, session_state: MutableMapping[str, Any], lang: str) -> str:
        cls.ensure_initialized(session_state)
        if lang in SUPPORTED_LANGS:
            session_state[cls.LANG_KEY] = lang
        return str(session_state[cls.LANG_KEY])

    @classmethod
    def get_page_key(cls, session_state: MutableMapping[str, Any]) -> str:
        cls.ensure_initialized(session_state)
        return str(session_state[cls.PAGE_KEY])

    @classmethod
    def set_page_key(cls, session_state: MutableMapping[str, Any], page_key: str) -> str:
        cls.ensure_initialized(session_state)
        if page_key in NAV_PAGE_KEYS:
            session_state[cls.PAGE_KEY] = page_key
        return str(session_state[cls.PAGE_KEY])

    @classmethod
    def set_flash_success(
        cls, session_state: MutableMapping[str, Any], message: str
    ) -> None:
        cls.ensure_initialized(session_state)
        session_state[cls.FLASH_SUCCESS_KEY] = message

    @classmethod
    def consume_flash_success(
        cls, session_state: MutableMapping[str, Any]
    ) -> str | None:
        cls.ensure_initialized(session_state)
        msg = session_state.get(cls.FLASH_SUCCESS_KEY)
        session_state[cls.FLASH_SUCCESS_KEY] = None
        return str(msg) if msg else None

    @classmethod
    def get_cart(cls, session_state: MutableMapping[str, Any]) -> dict[int, CartItem]:
        cls.ensure_initialized(session_state)
        return session_state[cls.CART_KEY]

    @classmethod
    def add_to_cart(
        cls,
        session_state: MutableMapping[str, Any],
        sales_service: SalesService,
        medicine_id: int,
        add_quantity: int,
    ) -> CartItem:
        cart = cls.get_cart(session_state)
        existing_qty = cart[medicine_id].quantity if medicine_id in cart else 0
        target_qty = existing_qty + int(add_quantity)
        (
            valid_id,
            name,
            batch,
            unit_price,
            available_stock,
            expiry_date,
        ) = sales_service.validate_medicine_for_cart(medicine_id, target_qty)

        item = CartItem(
            medicine_id=valid_id,
            medicine_name=name,
            batch_number=batch,
            unit_price=unit_price,
            quantity=target_qty,
            available_stock=available_stock,
            expiry_date=expiry_date,
        )
        cart[valid_id] = item
        return item

    @classmethod
    def update_cart_quantity(
        cls,
        session_state: MutableMapping[str, Any],
        sales_service: SalesService,
        medicine_id: int,
        new_quantity: int,
    ) -> None:
        cart = cls.get_cart(session_state)
        if new_quantity <= 0:
            cart.pop(medicine_id, None)
            return
        (
            valid_id,
            name,
            batch,
            unit_price,
            available_stock,
            expiry_date,
        ) = sales_service.validate_medicine_for_cart(medicine_id, new_quantity)
        cart[valid_id] = CartItem(
            medicine_id=valid_id,
            medicine_name=name,
            batch_number=batch,
            unit_price=unit_price,
            quantity=new_quantity,
            available_stock=available_stock,
            expiry_date=expiry_date,
        )

    @classmethod
    def remove_from_cart(
        cls, session_state: MutableMapping[str, Any], medicine_id: int
    ) -> None:
        cart = cls.get_cart(session_state)
        cart.pop(medicine_id, None)

    @classmethod
    def clear_cart(cls, session_state: MutableMapping[str, Any]) -> None:
        cls.ensure_initialized(session_state)
        session_state[cls.CART_KEY] = {}

    @classmethod
    def complete_sale_idempotent(
        cls,
        session_state: MutableMapping[str, Any],
        sales_service: SalesService,
        customer_name: str,
        customer_phone: str,
        discount_percent: object,
        tax_percent: object,
        amount_paid: object | None,
        payment_method: str,
        notes: str = "",
    ) -> tuple[Sale, bool]:
        """Execute checkout at most once per active transaction token across reruns.

        Returns (Sale, created_new: bool). If the same submission token replays during
        a Streamlit rerun, returns the already-created Sale without charging twice.
        """
        cls.ensure_initialized(session_state)
        token = str(session_state[cls.TOKEN_KEY])
        processed: dict[str, int] = session_state[cls.PROCESSED_TOKENS_KEY]

        if token in processed:
            existing = sales_service.get_sale(processed[token])
            if existing is not None:
                return existing, False

        items = list(cls.get_cart(session_state).values())
        sale = sales_service.create_sale(
            cart_items=items,
            customer_name=customer_name,
            customer_phone=customer_phone,
            discount_percent=discount_percent,
            tax_percent=tax_percent,
            amount_paid=amount_paid,
            payment_method=payment_method,
            notes=notes,
        )

        if sale.id is not None:
            processed[token] = sale.id
        session_state[cls.LAST_SALE_KEY] = sale
        session_state[cls.CART_KEY] = {}
        session_state[cls.TOKEN_KEY] = uuid.uuid4().hex
        return sale, True


class WebAppContainer:
    """Holds the cached web database backend and all shared domain services."""

    def __init__(
        self, db_path: str | Path | None = None, seed_if_empty: bool = True
    ) -> None:
        self.db = create_database_backend(db_path=db_path, seed_if_empty=seed_if_empty)
        self.supplier_service = SupplierService(self.db)
        self.inventory_service = InventoryService(self.db)
        self.sales_service = SalesService(self.db)
        self.report_service = ReportService(self.db)
        self.analytics_service = WebAnalyticsService(self.db)

    def close(self) -> None:
        self.db.close()
