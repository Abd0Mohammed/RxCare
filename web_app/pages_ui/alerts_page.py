"""Expiry Alerts page: quarantined expired batches, soon-to-expire batches, and low stock."""

from __future__ import annotations

import streamlit as st

from pharmacy.config import DEFAULT_EXPIRY_WARNING_DAYS
from pharmacy.utils import BusinessRuleError, ValidationError, days_until_expiry
from web_app.components.theme import render_kpi_card, render_page_header
from web_app.config import WEB_COLORS
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_alerts_page(app: WebAppContainer) -> None:
    """Render expired, expiring-soon, and low-stock alert workflows."""
    render_page_header(
        "Expiry & Stock Alerts",
        "Quarantine expired stock (blocked from POS checkout), rotate near-expiry batches, and restock low inventory.",
    )

    warning_days = st.selectbox(
        "Expiry Warning Window (Days)",
        options=[15, 30, 60, 90],
        index=[15, 30, 60, 90].index(DEFAULT_EXPIRY_WARNING_DAYS),
        key="alerts_window_days",
    )

    expired_meds = app.inventory_service.list_medicines(status_filter="expired")
    soon_meds = app.inventory_service.list_medicines(
        status_filter="expiring_soon", warning_days=int(warning_days)
    )
    low_meds = app.inventory_service.list_medicines(status_filter="low_stock")

    a1, a2, a3 = st.columns(3)
    with a1:
        render_kpi_card(
            "Expired (POS Blocked)",
            str(len(expired_meds)),
            accent=WEB_COLORS["danger"],
            subtext="Cannot be added to or sold via POS",
        )
    with a2:
        render_kpi_card(
            f"Expiring Within {warning_days} Days",
            str(len(soon_meds)),
            accent=WEB_COLORS["warning"],
            subtext="Prioritize FEFO dispensing",
        )
    with a3:
        render_kpi_card(
            "Low Stock Items",
            str(len(low_meds)),
            accent=WEB_COLORS["info"],
            subtext="At or below reorder level",
        )

    tab_exp, tab_soon, tab_low = st.tabs(
        [
            f"Expired ({len(expired_meds)})",
            f"Expiring Soon ({len(soon_meds)})",
            f"Low Stock ({len(low_meds)})",
        ]
    )

    with tab_exp:
        if expired_meds:
            st.error(
                "Safety Policy Active: Expired medicines are strictly blocked from sale in POS."
            )
            rows = [
                {
                    "ID": m.id,
                    "Medicine": m.name,
                    "Batch #": m.batch_number,
                    "Supplier": m.supplier_name,
                    "Remaining Qty": m.quantity,
                    "Expiry Date": m.expiry_date,
                    "Days Overdue": abs(days_until_expiry(m.expiry_date)),
                }
                for m in expired_meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            non_zero_expired = [m for m in expired_meds if m.quantity > 0 and m.id is not None]
            if non_zero_expired:
                st.subheader("Write Off Expired Stock")
                wo_map = {
                    f"#{m.id} — {m.name} (Batch {m.batch_number} | Qty: {m.quantity})": m
                    for m in non_zero_expired
                }
                chosen_wo = st.selectbox(
                    "Select Expired Batch to Write Off", list(wo_map.keys())
                )
                target = wo_map[chosen_wo]
                confirm_wo = st.checkbox(
                    f"Confirm writing off {target.quantity} unit(s) of '{target.name}' to 0",
                    key=f"confirm_wo_{target.id}",
                )
                if st.button(
                    "Write Off Expired Stock",
                    disabled=not confirm_wo,
                    type="primary",
                ):
                    assert target.id is not None
                    try:
                        app.inventory_service.write_off_expired_stock(target.id)
                        WebSessionController.set_flash_success(
                            st.session_state,
                            f"Wrote off expired stock for '{target.name}' (Batch {target.batch_number}).",
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(str(exc))
        else:
            st.success("No expired medicine batches in inventory.")

    with tab_soon:
        if soon_meds:
            rows = [
                {
                    "ID": m.id,
                    "Medicine": m.name,
                    "Batch #": m.batch_number,
                    "Supplier": m.supplier_name,
                    "Qty in Stock": m.quantity,
                    "Expiry Date": m.expiry_date,
                    "Days Remaining": days_until_expiry(m.expiry_date),
                }
                for m in soon_meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.success(f"No batches expiring within the next {warning_days} days.")

    with tab_low:
        if low_meds:
            rows = [
                {
                    "ID": m.id,
                    "Medicine": m.name,
                    "Batch #": m.batch_number,
                    "Supplier": m.supplier_name,
                    "Current Qty": m.quantity,
                    "Reorder Level": m.reorder_level,
                    "Expiry Date": m.expiry_date,
                }
                for m in low_meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            low_map = {
                f"#{m.id} — {m.name} (Current: {m.quantity} / Reorder: {m.reorder_level})": m
                for m in low_meds
                if m.id is not None
            }
            with st.form("alerts_quick_restock_form"):
                st.subheader("Quick Restock")
                chosen_low = st.selectbox("Medicine Batch", list(low_map.keys()))
                add_qty = st.number_input("Add Quantity", min_value=1, value=20, step=1)
                note = st.text_input("PO / Restock Reference", value="Low-stock replenishment")
                restock_btn = st.form_submit_button("Restock Batch", type="primary")
                if restock_btn:
                    target = low_map[chosen_low]
                    assert target.id is not None
                    try:
                        updated = app.inventory_service.restock_medicine(
                            target.id, int(add_qty), reference_note=note
                        )
                        WebSessionController.set_flash_success(
                            st.session_state,
                            f"Restocked '{updated.name}' to {updated.quantity} units.",
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(str(exc))
        else:
            st.success("No medicines are currently below their reorder threshold.")
