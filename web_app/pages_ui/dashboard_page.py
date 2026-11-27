"""Dashboard page: live pharmacy KPIs, profit metrics, alerts snapshot, and recent sales."""

from __future__ import annotations

import streamlit as st

from pharmacy.utils import format_currency, today_iso
from web_app.components.theme import (
    medicine_status_text,
    render_kpi_card,
    render_page_header,
)
from web_app.config import WEB_COLORS
from web_app.core.web_services import WebAppContainer


def render_dashboard_page(app: WebAppContainer) -> None:
    """Render the executive pharmacy dashboard."""
    render_page_header(
        "Pharmacy Dashboard",
        "Real-time operational overview across catalog inventory, expiry safety, sales, and profit.",
    )

    stats = app.report_service.get_dashboard_stats()
    today_profit = app.analytics_service.get_profit_summary(today_iso(), today_iso())
    all_profit = app.analytics_service.get_profit_summary()

    # Row 1: Core KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            "Total Medicines",
            str(stats.total_medicines),
            accent=WEB_COLORS["primary"],
            subtext=f"{stats.total_stock_units} total units in stock",
        )
    with c2:
        render_kpi_card(
            "Low-Stock Items",
            str(stats.low_stock_count),
            accent=WEB_COLORS["warning"],
            subtext="At or below reorder threshold",
        )
    with c3:
        render_kpi_card(
            "Expired Medicines",
            str(stats.expired_count),
            accent=WEB_COLORS["danger"],
            subtext="Blocked from POS checkout",
        )
    with c4:
        render_kpi_card(
            "Expiring Soon (30d)",
            str(stats.expiring_soon_count),
            accent=WEB_COLORS["warning"],
            subtext="Requires stock rotation",
        )

    # Row 2: Financial & Supplier KPIs
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        render_kpi_card(
            "Today's Sales",
            format_currency(stats.today_revenue),
            accent=WEB_COLORS["info"],
            subtext=f"{stats.today_sales_count} invoice(s) today",
        )
    with f2:
        render_kpi_card(
            "Total Profit (Net)",
            format_currency(all_profit.net_profit),
            accent=WEB_COLORS["success"],
            subtext=f"Today: {format_currency(today_profit.net_profit)}",
        )
    with f3:
        render_kpi_card(
            "Inventory Retail Value",
            format_currency(stats.inventory_retail_value),
            accent=WEB_COLORS["primary"],
            subtext=f"Cost basis: {format_currency(stats.inventory_cost_value)}",
        )
    with f4:
        render_kpi_card(
            "Active Suppliers",
            str(stats.total_suppliers),
            accent="#334155",
            subtext=f"All-time revenue: {format_currency(stats.total_revenue)}",
        )

    st.markdown("---")

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Urgent Stock & Expiry Alerts")
        seen: set[int] = set()
        alert_rows: list[dict[str, object]] = []
        for status_key in ("expired", "expiring_soon", "low_stock"):
            for med in app.inventory_service.list_medicines(status_filter=status_key):
                if med.id is not None and med.id not in seen:
                    seen.add(med.id)
                    alert_rows.append(
                        {
                            "Medicine": med.name,
                            "Batch": med.batch_number,
                            "Qty": med.quantity,
                            "Expiry": med.expiry_date,
                            "Status": medicine_status_text(med),
                        }
                    )
        if alert_rows:
            st.dataframe(alert_rows, use_container_width=True, hide_index=True)
        else:
            st.success("All inventory batches are healthy and sufficiently stocked.")

    with right_col:
        st.subheader("Recent Sales Invoices")
        recent_sales = app.sales_service.list_sales(limit=12)
        if recent_sales:
            sale_rows = [
                {
                    "Invoice #": s.invoice_number,
                    "Customer": s.customer_name,
                    "Payment": s.payment_method,
                    "Total": format_currency(s.total_amount),
                    "Timestamp": s.sale_date,
                }
                for s in recent_sales
            ]
            st.dataframe(sale_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No sales recorded yet.")
