"""Inventory Management page: bilingual stock monitoring, filters, adjustments, and audit log."""

from __future__ import annotations

import csv
import io
import streamlit as st

from pharmacy.utils import BusinessRuleError, ValidationError, format_currency
from web_app.components.theme import (
    medicine_status_text,
    render_kpi_card,
    render_page_header,
)
from web_app.config import WEB_COLORS
from web_app.core.i18n import (
    REASON_KEYS,
    localize_error,
    t,
    translate_category,
    translate_reason,
)
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_inventory_page(app: WebAppContainer, lang: str = "ar") -> None:
    """Render stock monitoring, filtering, adjustments, and stock audit log."""
    render_page_header(t("inv_title", lang), t("inv_subtitle", lang))

    stats = app.report_service.get_dashboard_stats()
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            t("inv_kpi_skus", lang), str(stats.total_medicines), WEB_COLORS["accent"]
        )
    with k2:
        render_kpi_card(
            t("inv_kpi_units", lang), str(stats.total_stock_units), WEB_COLORS["info"]
        )
    with k3:
        render_kpi_card(
            t("inv_kpi_low", lang), str(stats.low_stock_count), WEB_COLORS["warning"]
        )
    with k4:
        render_kpi_card(
            t("inv_kpi_cost", lang),
            format_currency(stats.inventory_cost_value),
            WEB_COLORS["success"],
        )

    tab_stock, tab_adjust, tab_audit = st.tabs(
        [t("inv_tab_levels", lang), t("inv_tab_adjust", lang), t("inv_tab_audit", lang)]
    )

    with tab_stock:
        c1, c2 = st.columns([2, 1.2])
        with c1:
            inv_search = st.text_input(
                t("inv_search_label", lang),
                placeholder=t("inv_search_ph", lang),
                key="inv_search",
            )
        with c2:
            inv_filter = st.selectbox(
                t("inv_filter_label", lang),
                [
                    (t("inv_filter_all", lang), "all"),
                    (t("inv_filter_low", lang), "low_stock"),
                    (t("inv_filter_sale", lang), "available_for_sale"),
                    (t("inv_filter_soon", lang), "expiring_soon"),
                    (t("inv_filter_exp", lang), "expired"),
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
                    t("col_id", lang): m.id,
                    t("col_medicine", lang): m.name,
                    t("col_batch", lang): m.batch_number,
                    t("col_category", lang): translate_category(m.category, lang),
                    t("col_qty", lang): m.quantity,
                    t("col_reorder", lang): m.reorder_level,
                    t("col_cost_val", lang): format_currency(
                        round(m.quantity * m.cost_price, 2)
                    ),
                    t("col_retail_val", lang): format_currency(
                        round(m.quantity * m.unit_price, 2)
                    ),
                    t("col_expiry", lang): m.expiry_date,
                    t("col_status", lang): medicine_status_text(m, lang=lang),
                }
                for m in meds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            csv_data = _medicines_to_csv_bytes(meds, lang)
            st.download_button(
                t("inv_download_csv", lang),
                data=csv_data,
                file_name="rxcare_inventory.csv",
                mime="text/csv",
            )
        else:
            st.info(t("inv_empty_filter", lang))

    with tab_adjust:
        all_meds = app.inventory_service.list_medicines()
        if not all_meds:
            st.info(t("inv_empty_adjust", lang))
        else:
            med_map = {
                f"#{m.id} — {m.name} ({m.batch_number} | {t('col_qty', lang)}: {m.quantity})": m
                for m in all_meds
                if m.id is not None
            }
            reason_choices = [(canonical, t(key, lang)) for canonical, key in REASON_KEYS]
            with st.form("inventory_adjust_form"):
                st.subheader(t("inv_adjust_heading", lang))
                chosen_label = st.selectbox(
                    t("inv_target_batch", lang), list(med_map.keys())
                )
                c1, c2 = st.columns(2)
                with c1:
                    delta = st.number_input(
                        t("inv_qty_delta", lang),
                        value=10,
                        step=1,
                    )
                with c2:
                    reason_pair = st.selectbox(
                        t("inv_reason_label", lang),
                        reason_choices,
                        format_func=lambda item: item[1],
                    )
                note = st.text_input(t("inv_ref_note", lang))
                submit_adj = st.form_submit_button(t("inv_btn_apply", lang), type="primary")

                if submit_adj:
                    target = med_map[chosen_label]
                    assert target.id is not None
                    try:
                        updated = app.inventory_service.adjust_stock(
                            medicine_id=target.id,
                            delta=int(delta),
                            reason=reason_pair[0],
                            reference_note=note,
                        )
                        WebSessionController.set_flash_success(
                            st.session_state,
                            t(
                                "inv_flash_adjusted",
                                lang,
                                name=updated.name,
                                qty=updated.quantity,
                            ),
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(localize_error(exc, lang))

    with tab_audit:
        adjustments = app.inventory_service.list_recent_adjustments(limit=100)
        if adjustments:
            audit_rows = [
                {
                    t("col_log_id", lang): a.id,
                    t("col_timestamp", lang): a.created_at,
                    t("col_medicine", lang): a.medicine_name,
                    t("col_change", lang): (
                        f"+{a.change_qty}" if a.change_qty > 0 else str(a.change_qty)
                    ),
                    t("col_reason", lang): translate_reason(a.reason, lang),
                    t("col_note", lang): a.reference_note,
                }
                for a in adjustments
            ]
            st.dataframe(audit_rows, use_container_width=True, hide_index=True)
        else:
            st.info(t("inv_audit_empty", lang))


def _medicines_to_csv_bytes(meds: list, lang: str = "ar") -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            t("col_id", lang),
            t("col_medicine", lang),
            t("col_generic", lang),
            t("col_category", lang),
            t("col_batch", lang),
            t("col_supplier", lang),
            t("col_cost", lang),
            t("col_price", lang),
            t("col_qty", lang),
            t("col_reorder", lang),
            t("col_expiry", lang),
        ]
    )
    for m in meds:
        writer.writerow(
            [
                m.id,
                m.name,
                m.generic_name,
                translate_category(m.category, lang),
                m.batch_number,
                m.supplier_name,
                m.cost_price,
                m.unit_price,
                m.quantity,
                m.reorder_level,
                m.expiry_date,
            ]
        )
    return buf.getvalue().encode("utf-8-sig")
