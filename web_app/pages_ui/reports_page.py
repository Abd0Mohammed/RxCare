"""Reports & Financial Analytics page: bilingual charts, profit summaries, and CSV export."""

from __future__ import annotations

import csv
import io
from datetime import timedelta

import matplotlib.pyplot as plt
import streamlit as st

from pharmacy.utils import ValidationError, format_currency, parse_iso_date, today_date
from web_app.components.charts import (
    build_category_value_figure,
    build_daily_sales_figure,
    build_top_medicines_figure,
)
from web_app.components.theme import render_kpi_card, render_page_header
from web_app.config import WEB_COLORS
from web_app.core.i18n import (
    localize_error,
    t,
    translate_category,
    translate_payment_method,
)
from web_app.core.web_services import WebAppContainer


def render_reports_page(app: WebAppContainer, lang: str = "ar") -> None:
    """Render sales, profit, inventory valuation, charts, and CSV downloads."""
    render_page_header(t("rep_title", lang), t("rep_subtitle", lang))

    today = today_date()
    default_start = today - timedelta(days=30)

    with st.form("reports_filter_form"):
        c1, c2, c3 = st.columns([1.2, 1.2, 1.0])
        with c1:
            start_input = st.date_input(t("rep_start_date", lang), value=default_start)
        with c2:
            end_input = st.date_input(t("rep_end_date", lang), value=today)
        with c3:
            st.write("")
            st.write("")
            st.form_submit_button(t("rep_btn_apply", lang), type="primary")

    if start_input is None or end_input is None:
        st.warning(t("rep_warn_dates", lang))
        return

    start_str = start_input.isoformat()
    end_str = end_input.isoformat()
    try:
        parse_iso_date(start_str, "Start date")
        parse_iso_date(end_str, "End date")
    except ValidationError as exc:
        st.error(localize_error(exc, lang))
        return

    if start_str > end_str:
        st.error(t("rep_err_range", lang))
        return

    summary = app.report_service.get_sales_summary_by_range(start_str, end_str)
    profit = app.analytics_service.get_profit_summary(start_str, end_str)
    dash_stats = app.report_service.get_dashboard_stats()
    daily_series = app.analytics_service.get_daily_sales_series(start_str, end_str)
    top_meds = app.report_service.get_top_selling_medicines(start_str, end_str, limit=15)
    cat_breakdown = app.report_service.get_category_inventory_breakdown()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card(
            t("rep_kpi_tx", lang),
            str(summary["invoice_count"]),
            accent=WEB_COLORS["info"],
        )
    with k2:
        render_kpi_card(
            t("rep_kpi_rev", lang),
            format_currency(float(summary["net_revenue"])),
            accent=WEB_COLORS["accent"],
            subtext=t(
                "rep_kpi_tax_sub",
                lang,
                amount=format_currency(float(summary["total_tax"])),
            ),
        )
    with k3:
        render_kpi_card(
            t("rep_kpi_profit", lang),
            format_currency(profit.net_profit),
            accent=WEB_COLORS["success"],
            subtext=t(
                "rep_kpi_cogs_sub",
                lang,
                amount=format_currency(profit.gross_cost),
            ),
        )
    with k4:
        render_kpi_card(
            t("rep_kpi_disc", lang),
            format_currency(float(summary["total_discount"])),
            accent=WEB_COLORS["warning"],
        )
    with k5:
        render_kpi_card(
            t("rep_kpi_inv", lang),
            format_currency(dash_stats.inventory_retail_value),
            accent="#737373",
            subtext=t(
                "rep_kpi_inv_cost_sub",
                lang,
                amount=format_currency(dash_stats.inventory_cost_value),
            ),
        )

    tab_daily, tab_best, tab_inv, tab_invoices = st.tabs(
        [
            t("rep_tab_daily", lang),
            t("rep_tab_best", lang),
            t("rep_tab_val", lang),
            t("rep_tab_invoices", lang),
        ]
    )

    with tab_daily:
        if daily_series:
            fig = build_daily_sales_figure(daily_series, lang=lang)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            table_rows = [
                {
                    t("col_date", lang): r["date"],
                    t("col_transactions", lang): r["invoice_count"],
                    t("col_revenue", lang): format_currency(float(r["revenue"])),
                    t("col_net_profit", lang): format_currency(float(r["profit"])),
                }
                for r in daily_series
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        else:
            st.info(t("rep_empty_daily", lang))

    with tab_best:
        if top_meds:
            fig = build_top_medicines_figure(top_meds, lang=lang)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            best_rows = [
                {
                    t("col_rank", lang): idx,
                    t("col_medicine", lang): r["medicine_name"],
                    t("col_batch", lang): r["batch_number"],
                    t("col_units_sold", lang): r["units_sold"],
                    t("col_gross_revenue", lang): format_currency(float(r["total_revenue"])),
                }
                for idx, r in enumerate(top_meds, start=1)
            ]
            st.dataframe(best_rows, use_container_width=True, hide_index=True)
        else:
            st.info(t("rep_empty_best", lang))

    with tab_inv:
        if cat_breakdown:
            fig = build_category_value_figure(cat_breakdown, lang=lang)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            cat_rows = [
                {
                    t("col_category", lang): translate_category(str(r["category"]), lang),
                    t("col_sku_count", lang): r["sku_count"],
                    t("col_total", lang): r["total_units"],
                    t("col_retail_val", lang): format_currency(float(r["retail_value"])),
                }
                for r in cat_breakdown
            ]
            st.dataframe(cat_rows, use_container_width=True, hide_index=True)
        else:
            st.info(t("rep_empty_inv", lang))

    with tab_invoices:
        sales_list = app.sales_service.list_sales(start_date=start_str, end_date=end_str)
        if sales_list:
            inv_rows = [
                {
                    t("col_id", lang): s.id,
                    t("col_invoice", lang): s.invoice_number,
                    t("col_timestamp", lang): s.sale_date,
                    t("col_customer", lang): s.customer_name,
                    t("col_payment", lang): translate_payment_method(s.payment_method, lang),
                    t("col_subtotal", lang): format_currency(s.subtotal),
                    t("col_discount", lang): format_currency(s.discount_amount),
                    t("col_tax", lang): format_currency(s.tax_amount),
                    t("col_grand_total", lang): format_currency(s.total_amount),
                }
                for s in sales_list
            ]
            st.dataframe(inv_rows, use_container_width=True, hide_index=True)

            st.download_button(
                t("rep_download_csv", lang),
                data=_sales_to_csv_bytes(sales_list, lang),
                file_name=f"rxcare_sales_{start_str}_to_{end_str}.csv",
                mime="text/csv",
            )
        else:
            st.info(t("rep_empty_invoices", lang))


def _sales_to_csv_bytes(sales_list: list, lang: str = "ar") -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            t("col_invoice", lang),
            t("col_timestamp", lang),
            t("col_customer", lang),
            t("col_phone", lang),
            t("col_payment", lang),
            t("col_subtotal", lang),
            t("col_discount", lang),
            t("col_tax", lang),
            t("col_grand_total", lang),
            t("pos_amount_paid", lang),
            t("pos_change_due", lang),
        ]
    )
    for s in sales_list:
        writer.writerow(
            [
                s.invoice_number,
                s.sale_date,
                s.customer_name,
                s.customer_phone,
                translate_payment_method(s.payment_method, lang),
                s.subtotal,
                s.discount_amount,
                s.tax_amount,
                s.total_amount,
                s.amount_paid,
                s.change_due,
            ]
        )
    return buf.getvalue().encode("utf-8-sig")
