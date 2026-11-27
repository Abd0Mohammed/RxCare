"""Reports & Analytics page: daily sales, profit, best-sellers, inventory value, and charts."""

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
from web_app.core.web_services import WebAppContainer


def render_reports_page(app: WebAppContainer) -> None:
    """Render sales, profit, inventory valuation, charts, and CSV downloads."""
    render_page_header(
        "Reports & Financial Analytics",
        "Analyze daily sales, revenue, net profit, best-selling medicines, and category inventory value.",
    )

    today = today_date()
    default_start = today - timedelta(days=30)

    with st.form("reports_filter_form"):
        c1, c2, c3 = st.columns([1.2, 1.2, 1.0])
        with c1:
            start_input = st.date_input("Start Date", value=default_start)
        with c2:
            end_input = st.date_input("End Date", value=today)
        with c3:
            st.write("")
            st.write("")
            st.form_submit_button("Apply Date Filter", type="primary")

    if start_input is None or end_input is None:
        st.warning("Please select both a Start Date and an End Date.")
        return

    start_str = start_input.isoformat()
    end_str = end_input.isoformat()
    try:
        parse_iso_date(start_str, "Start date")
        parse_iso_date(end_str, "End date")
    except ValidationError as exc:
        st.error(str(exc))
        return

    if start_str > end_str:
        st.error("Start Date cannot be later than End Date.")
        return

    summary = app.report_service.get_sales_summary_by_range(start_str, end_str)
    profit = app.analytics_service.get_profit_summary(start_str, end_str)
    dash_stats = app.report_service.get_dashboard_stats()
    daily_series = app.analytics_service.get_daily_sales_series(start_str, end_str)
    top_meds = app.report_service.get_top_selling_medicines(start_str, end_str, limit=15)
    cat_breakdown = app.report_service.get_category_inventory_breakdown()

    # Summary KPI Strip
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card(
            "Transactions",
            str(summary["invoice_count"]),
            accent=WEB_COLORS["info"],
        )
    with k2:
        render_kpi_card(
            "Total Revenue",
            format_currency(float(summary["net_revenue"])),
            accent=WEB_COLORS["primary"],
            subtext=f"Tax: {format_currency(float(summary['total_tax']))}",
        )
    with k3:
        render_kpi_card(
            "Total Profit (Net)",
            format_currency(profit.net_profit),
            accent=WEB_COLORS["success"],
            subtext=f"COGS: {format_currency(profit.gross_cost)}",
        )
    with k4:
        render_kpi_card(
            "Discounts Given",
            format_currency(float(summary["total_discount"])),
            accent=WEB_COLORS["warning"],
        )
    with k5:
        render_kpi_card(
            "Inventory Value",
            format_currency(dash_stats.inventory_retail_value),
            accent="#334155",
            subtext=f"Cost: {format_currency(dash_stats.inventory_cost_value)}",
        )

    tab_daily, tab_best, tab_inv, tab_invoices = st.tabs(
        ["Daily Sales & Profit", "Best-Selling Medicines", "Inventory Valuation", "Invoice History"]
    )

    with tab_daily:
        if daily_series:
            fig = build_daily_sales_figure(daily_series)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            table_rows = [
                {
                    "Date": r["date"],
                    "Transactions": r["invoice_count"],
                    "Revenue": format_currency(float(r["revenue"])),
                    "Net Profit": format_currency(float(r["profit"])),
                }
                for r in daily_series
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No sales transactions found in the selected date range.")

    with tab_best:
        if top_meds:
            fig = build_top_medicines_figure(top_meds)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            best_rows = [
                {
                    "Rank": idx,
                    "Medicine": r["medicine_name"],
                    "Batch #": r["batch_number"],
                    "Units Sold": r["units_sold"],
                    "Gross Revenue": format_currency(float(r["total_revenue"])),
                }
                for idx, r in enumerate(top_meds, start=1)
            ]
            st.dataframe(best_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No item sales found in the selected date range.")

    with tab_inv:
        if cat_breakdown:
            fig = build_category_value_figure(cat_breakdown)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            cat_rows = [
                {
                    "Category": r["category"],
                    "SKU Count": r["sku_count"],
                    "Total Stock Units": r["total_units"],
                    "Retail Value": format_currency(float(r["retail_value"])),
                }
                for r in cat_breakdown
            ]
            st.dataframe(cat_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No inventory records found.")

    with tab_invoices:
        sales_list = app.sales_service.list_sales(start_date=start_str, end_date=end_str)
        if sales_list:
            inv_rows = [
                {
                    "ID": s.id,
                    "Invoice #": s.invoice_number,
                    "Timestamp": s.sale_date,
                    "Customer": s.customer_name,
                    "Method": s.payment_method,
                    "Subtotal": format_currency(s.subtotal),
                    "Discount": format_currency(s.discount_amount),
                    "Tax": format_currency(s.tax_amount),
                    "Grand Total": format_currency(s.total_amount),
                }
                for s in sales_list
            ]
            st.dataframe(inv_rows, use_container_width=True, hide_index=True)

            st.download_button(
                "Download Sales CSV",
                data=_sales_to_csv_bytes(sales_list),
                file_name=f"rxcare_sales_{start_str}_to_{end_str}.csv",
                mime="text/csv",
            )
        else:
            st.info("No invoices found for the selected date range.")


def _sales_to_csv_bytes(sales_list: list) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
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
    )
    for s in sales_list:
        writer.writerow(
            [
                s.invoice_number,
                s.sale_date,
                s.customer_name,
                s.customer_phone,
                s.payment_method,
                s.subtotal,
                s.discount_amount,
                s.tax_amount,
                s.total_amount,
                s.amount_paid,
                s.change_due,
            ]
        )
    return buf.getvalue().encode("utf-8")
