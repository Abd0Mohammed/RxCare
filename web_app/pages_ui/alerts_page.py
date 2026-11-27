"""Expiry Alerts page: bilingual quarantine, near-expiry rotation, and low-stock restocking."""

from __future__ import annotations

import streamlit as st

from pharmacy.config import DEFAULT_EXPIRY_WARNING_DAYS
from pharmacy.utils import BusinessRuleError, ValidationError, days_until_expiry
from web_app.components.theme import render_kpi_card, render_page_header
from web_app.config import WEB_COLORS
from web_app.core.i18n import localize_error, t
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_alerts_page(app: WebAppContainer, lang: str = "ar") -> None:
    """Render expired, expiring-soon, and low-stock alert workflows."""
    render_page_header(t("al_title", lang), t("al_subtitle", lang))

    warning_days = st.selectbox(
        t("al_window_label", lang),
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
            t("al_kpi_expired", lang),
            str(len(expired_meds)),
            accent=WEB_COLORS["danger"],
            subtext=t("al_kpi_expired_sub", lang),
        )
    with a2:
        render_kpi_card(
            t("al_kpi_soon", lang, days=warning_days),
            str(len(soon_meds)),
            accent=WEB_COLORS["warning"],
            subtext=t("al_kpi_soon_sub", lang),
        )
    with a3:
        render_kpi_card(
            t("al_kpi_low", lang),
            str(len(low_meds)),
            accent=WEB_COLORS["info"],
            subtext=t("al_kpi_low_sub", lang),
        )

    tab_exp, tab_soon, tab_low = st.tabs(
        [
            t("al_tab_exp", lang, count=len(expired_meds)),
            t("al_tab_soon", lang, count=len(soon_meds)),
            t("al_tab_low", lang, count=len(low_meds)),
        ]
    )

    with tab_exp:
        if expired_meds:
            st.error(t("al_safety_banner", lang))
            rows = [
                {
                    t("col_id", lang): m.id,
                    t("col_medicine", lang): m.name,
                    t("col_batch", lang): m.batch_number,
                    t("col_supplier", lang): m.supplier_name,
                    t("col_remaining_qty", lang): m.quantity,
                    t("col_expiry", lang): m.expiry_date,
                    t("col_days_overdue", lang): abs(days_until_expiry(m.expiry_date)),
                }
                for m in expired_meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            non_zero_expired = [
                m for m in expired_meds if m.quantity > 0 and m.id is not None
            ]
            if non_zero_expired:
                st.subheader(t("al_writeoff_heading", lang))
                wo_map = {
                    f"#{m.id} — {m.name} ({m.batch_number} | {t('col_qty', lang)}: {m.quantity})": m
                    for m in non_zero_expired
                }
                chosen_wo = st.selectbox(t("al_writeoff_select", lang), list(wo_map.keys()))
                target = wo_map[chosen_wo]
                confirm_wo = st.checkbox(
                    t(
                        "al_writeoff_confirm",
                        lang,
                        qty=target.quantity,
                        name=target.name,
                    ),
                    key=f"confirm_wo_{target.id}",
                )
                if st.button(
                    t("al_btn_writeoff", lang),
                    disabled=not confirm_wo,
                    type="primary",
                ):
                    assert target.id is not None
                    try:
                        app.inventory_service.write_off_expired_stock(target.id)
                        WebSessionController.set_flash_success(
                            st.session_state,
                            t(
                                "al_flash_writeoff",
                                lang,
                                name=target.name,
                                batch=target.batch_number,
                            ),
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(localize_error(exc, lang))
        else:
            st.success(t("al_none_expired", lang))

    with tab_soon:
        if soon_meds:
            rows = [
                {
                    t("col_id", lang): m.id,
                    t("col_medicine", lang): m.name,
                    t("col_batch", lang): m.batch_number,
                    t("col_supplier", lang): m.supplier_name,
                    t("col_qty", lang): m.quantity,
                    t("col_expiry", lang): m.expiry_date,
                    t("col_days_left", lang): days_until_expiry(m.expiry_date),
                }
                for m in soon_meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.success(t("al_none_soon", lang, days=warning_days))

    with tab_low:
        if low_meds:
            rows = [
                {
                    t("col_id", lang): m.id,
                    t("col_medicine", lang): m.name,
                    t("col_batch", lang): m.batch_number,
                    t("col_supplier", lang): m.supplier_name,
                    t("col_current_qty", lang): m.quantity,
                    t("col_reorder", lang): m.reorder_level,
                    t("col_expiry", lang): m.expiry_date,
                }
                for m in low_meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            low_map = {
                f"#{m.id} — {m.name} ({m.quantity} / {m.reorder_level})": m
                for m in low_meds
                if m.id is not None
            }
            with st.form("alerts_quick_restock_form"):
                st.subheader(t("al_quick_restock", lang))
                chosen_low = st.selectbox(t("col_medicine", lang), list(low_map.keys()))
                add_qty = st.number_input(t("al_add_qty", lang), min_value=1, value=20, step=1)
                note = st.text_input(
                    t("al_po_ref", lang), value=t("al_po_default", lang)
                )
                restock_btn = st.form_submit_button(t("al_btn_restock", lang), type="primary")
                if restock_btn:
                    target = low_map[chosen_low]
                    assert target.id is not None
                    try:
                        updated = app.inventory_service.restock_medicine(
                            target.id, int(add_qty), reference_note=note
                        )
                        WebSessionController.set_flash_success(
                            st.session_state,
                            t(
                                "al_flash_restocked",
                                lang,
                                name=updated.name,
                                qty=updated.quantity,
                            ),
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(localize_error(exc, lang))
        else:
            st.success(t("al_none_low", lang))
