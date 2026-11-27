"""Inventory Management page: stock monitoring, low-stock alerts, adjustments, and audit log."""

from __future__ import annotations

import streamlit as st

from pharmacy.utils import BusinessRuleError, ValidationError, format_currency
from web_app.components.theme import (
    medicine_status_text,
    render_kpi_card,
    render_page_header,
)
from web_app.config import WEB_COLORS
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_inventory_page(app: WebAppContainer) -> None:
    """Render stock monitoring, filtering, adjustments, and stock audit log."""
    render_page_header(
        "Inventory Management",
        "Monitor live batch quantities, address low-stock alerts, and log audited stock adjustments.",
    )

    stats = app.report_service.get_dashboard_stats()
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Total SKUs", str(stats.total_medicines), WEB_COLORS["primary"])
    with k2:
        render_kpi_card("Total Stock Units", str(stats.total_stock_units), WEB_COLORS["info"])
    with k3:
        render_kpi_card("Low Stock Alerts", str(stats.low_stock_count), WEB_COLORS["warning"])
    with k4:
        render_kpi_card(
            "Inventory Cost Value",
            format_currency(stats.inventory_cost_value),
            WEB_COLORS["success"],
        )

    tab_stock, tab_adjust, tab_audit = st.tabs(
        ["Stock Levels & Filters", "Restock / Adjust Stock", "Stock Audit Log"]
    )

    with tab_stock:
        c1, c2 = st.columns([2, 1.2])
        with c1:
            inv_search = st.text_input(
                "Search Inventory",
                placeholder="Medicine, batch #, or supplier...",
                key="inv_search",
            )
        with c2:
            inv_filter = st.selectbox(
                "Filter Inventory",
                [
                    ("All Stock", "all"),
                    ("Low Stock Only", "low_stock"),
                    ("Available for Sale", "available_for_sale"),
                    ("Expiring Soon", "expiring_soon"),
                    ("Expired", "expired"),
                ],
                format_func=lambda x: x[0],
                key="inv_filter",
            )

        meds = app.inventory_service.list_medicines(
            search_query=inv_search, status_filter=inv_filter[1]
        )
        if meds:
            rows = [
                {
                    "ID": m.id,
                    "Medicine": m.name,
                    "Batch #": m.batch_number,
                    "Category": m.category,
                    "Qty": m.quantity,
                    "Reorder Level": m.reorder_level,
                    "Cost Value": format_currency(round(m.quantity * m.cost_price, 2)),
                    "Retail Value": format_currency(round(m.quantity * m.unit_price, 2)),
                    "Expiry": m.expiry_date,
                    "Status": medicine_status_text(m),
                }
                for m in meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            csv_data = _medicines_to_csv_bytes(meds)
            st.download_button(
                "Download Inventory CSV",
                data=csv_data,
                file_name="rxcare_inventory.csv",
                mime="text/csv",
            )
        else:
            st.info("No inventory batches match the selected filter.")

    with tab_adjust:
        all_meds = app.inventory_service.list_medicines()
        if not all_meds:
            st.info("No medicines in inventory to adjust.")
        else:
            med_map = {
                f"#{m.id} — {m.name} (Batch {m.batch_number} | Stock: {m.quantity})": m
                for m in all_meds
                if m.id is not None
            }
            with st.form("inventory_adjust_form"):
                st.subheader("Record Stock Adjustment")
                chosen_label = st.selectbox("Target Medicine Batch", list(med_map.keys()))
                c1, c2 = st.columns(2)
                with c1:
                    delta = st.number_input(
                        "Quantity Change (+ restock / - deduction)",
                        value=10,
                        step=1,
                    )
                with c2:
                    reason = st.selectbox(
                        "Adjustment Reason",
                        [
                            "Restock",
                            "Supplier Return",
                            "Damage / Spoilage",
                            "Audit Correction",
                        ],
                    )
                note = st.text_input("Reference Note (PO #, invoice, or audit ref)")
                submit_adj = st.form_submit_button("Apply Stock Adjustment", type="primary")

                if submit_adj:
                    target = med_map[chosen_label]
                    assert target.id is not None
                    try:
                        updated = app.inventory_service.adjust_stock(
                            medicine_id=target.id,
                            delta=int(delta),
                            reason=reason,
                            reference_note=note,
                        )
                        WebSessionController.set_flash_success(
                            st.session_state,
                            f"Updated '{updated.name}' stock to {updated.quantity} units.",
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(str(exc))

    with tab_audit:
        adjustments = app.inventory_service.list_recent_adjustments(limit=100)
        if adjustments:
            audit_rows = [
                {
                    "Log ID": a.id,
                    "Timestamp": a.created_at,
                    "Medicine": a.medicine_name,
                    "Change": f"+{a.change_qty}" if a.change_qty > 0 else str(a.change_qty),
                    "Reason": a.reason,
                    "Reference Note": a.reference_note,
                }
                for a in adjustments
            ]
            st.dataframe(audit_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No stock adjustments recorded yet.")


def _medicines_to_csv_bytes(meds: list) -> bytes:
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "ID",
            "Name",
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
    )
    for m in meds:
        writer.writerow(
            [
                m.id,
                m.name,
                m.generic_name,
                m.category,
                m.batch_number,
                m.supplier_name,
                m.cost_price,
                m.unit_price,
                m.quantity,
                m.reorder_level,
                m.expiry_date,
            ]
        )
    return buf.getvalue().encode("utf-8")
