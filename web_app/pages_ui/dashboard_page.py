"""Dashboard page: bilingual dark-first KPIs, profit metrics, alerts snapshot, and recent sales."""

from __future__ import annotations

import streamlit as st

from pharmacy.utils import format_currency, today_iso
from web_app.components.theme import (
    medicine_status_text,
    render_kpi_card,
    render_page_header,
)
from web_app.config import WEB_COLORS
from web_app.core.i18n import t, translate_payment_method
from web_app.core.web_services import WebAppContainer


def render_dashboard_page(app: WebAppContainer, lang: str = "ar") -> None:
    """Render the executive pharmacy dashboard."""
    render_page_header(t("dash_title", lang), t("dash_subtitle", lang))

    stats = app.report_service.get_dashboard_stats()
    today_profit = app.analytics_service.get_profit_summary(today_iso(), today_iso())
    all_profit = app.analytics_service.get_profit_summary()

    # Row 1: Core KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card(
            t("kpi_total_medicines", lang),
            str(stats.total_medicines),
            accent=WEB_COLORS["accent"],
            subtext=t("kpi_total_units_sub", lang, units=stats.total_stock_units),
        )
    with c2:
        render_kpi_card(
            t("kpi_low_stock", lang),
            str(stats.low_stock_count),
            accent=WEB_COLORS["warning"],
            subtext=t("kpi_low_stock_sub", lang),
        )
    with c3:
        render_kpi_card(
            t("kpi_expired", lang),
            str(stats.expired_count),
            accent=WEB_COLORS["danger"],
            subtext=t("kpi_expired_sub", lang),
        )
    with c4:
        render_kpi_card(
            t("kpi_expiring_soon", lang),
            str(stats.expiring_soon_count),
            accent=WEB_COLORS["warning"],
            subtext=t("kpi_expiring_soon_sub", lang),
        )

    # Row 2: Financial & Supplier KPIs
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        render_kpi_card(
            t("kpi_today_sales", lang),
            format_currency(stats.today_revenue),
            accent=WEB_COLORS["info"],
            subtext=t("kpi_today_invoices_sub", lang, count=stats.today_sales_count),
        )
    with f2:
        render_kpi_card(
            t("kpi_total_profit", lang),
            format_currency(all_profit.net_profit),
            accent=WEB_COLORS["success"],
            subtext=t("kpi_today_profit_sub", lang, amount=format_currency(today_profit.net_profit)),
        )
    with f3:
        render_kpi_card(
            t("kpi_retail_value", lang),
            format_currency(stats.inventory_retail_value),
            accent=WEB_COLORS["accent"],
            subtext=t("kpi_cost_basis_sub", lang, amount=format_currency(stats.inventory_cost_value)),
        )
    with f4:
        render_kpi_card(
            t("kpi_suppliers", lang),
            str(stats.total_suppliers),
            accent="#737373",
            subtext=t("kpi_all_time_rev_sub", lang, amount=format_currency(stats.total_revenue)),
        )

    st.markdown("---")

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader(t("dash_urgent_alerts", lang))
        seen: set[int] = set()
        alert_rows: list[dict[str, object]] = []
        for status_key in ("expired", "expiring_soon", "low_stock"):
            for med in app.inventory_service.list_medicines(status_filter=status_key):
                if med.id is not None and med.id not in seen:
                    seen.add(med.id)
                    alert_rows.append(
                        {
                            t("col_medicine", lang): med.name,
                            t("col_batch", lang): med.batch_number,
                            t("col_qty", lang): med.quantity,
                            t("col_expiry", lang): med.expiry_date,
                            t("col_status", lang): medicine_status_text(med, lang=lang),
                        }
                    )
        if alert_rows:
            st.dataframe(alert_rows, use_container_width=True, hide_index=True)
        else:
            st.success(t("dash_alerts_healthy", lang))

    with right_col:
        st.subheader(t("dash_recent_sales", lang))
        recent_sales = app.sales_service.list_sales(limit=12)
        if recent_sales:
            sale_rows = [
                {
                    t("col_invoice", lang): s.invoice_number,
                    t("col_customer", lang): s.customer_name,
                    t("col_payment", lang): translate_payment_method(s.payment_method, lang),
                    t("col_total", lang): format_currency(s.total_amount),
                    t("col_timestamp", lang): s.sale_date,
                }
                for s in recent_sales
            ]
            st.dataframe(sale_rows, use_container_width=True, hide_index=True)
        else:
            st.info(t("dash_no_sales", lang))
