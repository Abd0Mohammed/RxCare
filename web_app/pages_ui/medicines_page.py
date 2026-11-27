"""Medicine Management page: bilingual CRUD, search, category filter, and detail viewer."""

from __future__ import annotations

import streamlit as st

from pharmacy.config import DEFAULT_LOW_STOCK_THRESHOLD
from pharmacy.utils import (
    BusinessRuleError,
    ValidationError,
    format_currency,
    today_iso,
)
from web_app.components.theme import medicine_status_text, render_page_header
from web_app.core.i18n import localize_error, t, translate_category
from web_app.core.web_services import WebAppContainer, WebSessionController

DEFAULT_CATEGORIES = [
    "Analgesics",
    "Antibiotics",
    "Antihistamines",
    "Cardiovascular",
    "Dermatology",
    "Endocrinology",
    "Gastrointestinal",
    "Respiratory",
    "Vitamins & Supplements",
    "General",
]


def render_medicines_page(app: WebAppContainer, lang: str = "ar") -> None:
    """Render medicine catalog management with search, category filter, and CRUD tabs."""
    render_page_header(t("med_title", lang), t("med_subtitle", lang))

    tab_catalog, tab_add, tab_edit = st.tabs(
        [t("med_tab_catalog", lang), t("med_tab_add", lang), t("med_tab_edit", lang)]
    )

    # ── TAB 1: Catalog Search, Category Filter & Detail Viewer ────────────────
    with tab_catalog:
        canonical_cats = sorted(
            set(DEFAULT_CATEGORIES)
            | set(app.analytics_service.list_categories(app.inventory_service))
        )
        cat_choices: list[tuple[str, str]] = [("All Categories", t("all_categories", lang))] + [
            (cat, translate_category(cat, lang)) for cat in canonical_cats
        ]

        f1, f2, f3 = st.columns([2, 1.3, 1.3])
        with f1:
            search_q = st.text_input(
                t("med_search_label", lang),
                placeholder=t("med_search_ph", lang),
                key="med_search_q",
            )
        with f2:
            selected_cat_pair = st.selectbox(
                t("med_filter_cat", lang),
                cat_choices,
                format_func=lambda item: item[1],
                key="med_cat_filter",
            )
        with f3:
            status_opt = st.selectbox(
                t("med_filter_avail", lang),
                [
                    (t("avail_all", lang), "all"),
                    (t("avail_sale", lang), "available_for_sale"),
                    (t("avail_low", lang), "low_stock"),
                    (t("avail_soon", lang), "expiring_soon"),
                    (t("avail_expired", lang), "expired"),
                ],
                format_func=lambda item: item[0],
                key="med_status_filter",
            )

        medicines = app.analytics_service.filter_medicines(
            app.inventory_service,
            search_query=search_q,
            status_filter=status_opt[1],
            category=selected_cat_pair[0],
        )

        if medicines:
            rows = [
                {
                    t("col_id", lang): m.id,
                    t("col_medicine", lang): m.name,
                    t("col_generic", lang): m.generic_name,
                    t("col_category", lang): translate_category(m.category, lang),
                    t("col_batch", lang): m.batch_number,
                    t("col_supplier", lang): m.supplier_name,
                    t("col_cost", lang): format_currency(m.cost_price),
                    t("col_price", lang): format_currency(m.unit_price),
                    t("col_qty", lang): m.quantity,
                    t("col_expiry", lang): m.expiry_date,
                    t("col_status", lang): medicine_status_text(m, lang=lang),
                }
                for m in medicines
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            st.subheader(t("med_details_heading", lang))
            med_lookup = {
                f"#{m.id} — {m.name} ({m.batch_number})": m
                for m in medicines
                if m.id is not None
            }
            chosen_label = st.selectbox(
                t("med_inspect_label", lang),
                list(med_lookup.keys()),
                key="med_inspect_select",
            )
            chosen = med_lookup[chosen_label]
            d1, d2, d3, d4 = st.columns(4)
            d1.metric(t("col_price", lang), format_currency(chosen.unit_price))
            d2.metric(t("col_cost", lang), format_currency(chosen.cost_price))
            d3.metric(
                t("med_unit_margin", lang),
                format_currency(round(chosen.unit_price - chosen.cost_price, 2)),
            )
            d4.metric(
                t("med_stock_reorder", lang), f"{chosen.quantity} / {chosen.reorder_level}"
            )
            st.caption(
                f"{t('col_generic', lang)}: {chosen.generic_name or t('not_available', lang)} | "
                f"{t('col_category', lang)}: {translate_category(chosen.category, lang)} | "
                f"{t('col_supplier', lang)}: {chosen.supplier_name} | "
                f"{t('col_expiry', lang)}: {chosen.expiry_date} ({medicine_status_text(chosen, lang=lang)})"
            )
            if chosen.description:
                st.info(chosen.description)
        else:
            st.info(t("med_empty_filter", lang))

    # ── TAB 2: Add Medicine ───────────────────────────────────────────────────
    with tab_add:
        suppliers = app.supplier_service.list_suppliers()
        unassigned_lbl = t("unassigned", lang)
        supplier_map: dict[str, int | None] = {unassigned_lbl: None}
        for sup in suppliers:
            if sup.id is not None:
                supplier_map[sup.name] = sup.id

        add_cat_choices = [(cat, translate_category(cat, lang)) for cat in DEFAULT_CATEGORIES]

        with st.form("add_medicine_form", clear_on_submit=True):
            st.subheader(t("med_add_heading", lang))
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(t("med_field_name", lang))
                generic = st.text_input(t("med_field_generic", lang))
                category_pair = st.selectbox(
                    t("med_field_category", lang),
                    add_cat_choices,
                    index=9,
                    format_func=lambda item: item[1],
                )
                batch = st.text_input(t("med_field_batch", lang))
                supplier_label = st.selectbox(
                    t("med_field_supplier", lang), list(supplier_map.keys())
                )
            with c2:
                cost_price = st.number_input(
                    t("med_field_cost", lang), min_value=0.0, step=0.25, format="%.2f"
                )
                unit_price = st.number_input(
                    t("med_field_price", lang),
                    min_value=0.01,
                    value=5.00,
                    step=0.25,
                    format="%.2f",
                )
                quantity = st.number_input(
                    t("med_field_qty", lang), min_value=0, value=20, step=1
                )
                reorder_level = st.number_input(
                    t("med_field_reorder", lang),
                    min_value=0,
                    value=DEFAULT_LOW_STOCK_THRESHOLD,
                    step=1,
                )
                expiry_date = st.text_input(
                    t("med_field_expiry", lang), value=today_iso()
                )

            description = st.text_area(t("med_field_desc", lang), height=70)
            submitted = st.form_submit_button(t("med_btn_add", lang), type="primary")

            if submitted:
                try:
                    created = app.inventory_service.create_medicine(
                        name=name,
                        generic_name=generic,
                        category=category_pair[0],
                        batch_number=batch,
                        supplier_id=supplier_map[supplier_label],
                        cost_price=cost_price,
                        unit_price=unit_price,
                        quantity=int(quantity),
                        reorder_level=int(reorder_level),
                        expiry_date=expiry_date,
                        description=description,
                    )
                    WebSessionController.set_flash_success(
                        st.session_state,
                        t(
                            "med_flash_added",
                            lang,
                            name=created.name,
                            batch=created.batch_number,
                        ),
                    )
                    st.rerun()
                except (ValidationError, BusinessRuleError) as exc:
                    st.error(localize_error(exc, lang))

    # ── TAB 3: Edit or Delete Medicine ────────────────────────────────────────
    with tab_edit:
        all_meds = app.inventory_service.list_medicines()
        if not all_meds:
            st.info(t("med_none_edit", lang))
            return

        edit_map = {
            f"#{m.id} — {m.name} ({m.batch_number})": m
            for m in all_meds
            if m.id is not None
        }
        selected_key = st.selectbox(
            t("med_select_modify", lang), list(edit_map.keys()), key="med_edit_select"
        )
        target = edit_map[selected_key]

        suppliers = app.supplier_service.list_suppliers()
        unassigned_lbl = t("unassigned", lang)
        supplier_map = {unassigned_lbl: None}
        default_sup_label = unassigned_lbl
        for sup in suppliers:
            if sup.id is not None:
                supplier_map[sup.name] = sup.id
                if sup.id == target.supplier_id:
                    default_sup_label = sup.name

        cat_options = list(dict.fromkeys(DEFAULT_CATEGORIES + [target.category]))
        edit_cat_choices = [(cat, translate_category(cat, lang)) for cat in cat_options]

        with st.form(f"edit_medicine_form_{target.id}"):
            st.subheader(
                t("med_editing_heading", lang, name=target.name, batch=target.batch_number)
            )
            c1, c2 = st.columns(2)
            with c1:
                e_name = st.text_input(t("med_field_name", lang), value=target.name)
                e_generic = st.text_input(
                    t("med_field_generic", lang), value=target.generic_name
                )
                e_cat_pair = st.selectbox(
                    t("med_field_category", lang),
                    edit_cat_choices,
                    index=cat_options.index(target.category),
                    format_func=lambda item: item[1],
                )
                e_batch = st.text_input(t("med_field_batch", lang), value=target.batch_number)
                sup_keys = list(supplier_map.keys())
                e_supplier = st.selectbox(
                    t("med_field_supplier", lang),
                    sup_keys,
                    index=sup_keys.index(default_sup_label),
                )
            with c2:
                e_cost = st.number_input(
                    t("med_field_cost", lang),
                    min_value=0.0,
                    value=float(target.cost_price),
                    step=0.25,
                    format="%.2f",
                )
                e_price = st.number_input(
                    t("med_field_price", lang),
                    min_value=0.01,
                    value=max(0.01, float(target.unit_price)),
                    step=0.25,
                    format="%.2f",
                )
                e_qty = st.number_input(
                    t("med_field_qty", lang),
                    min_value=0,
                    value=int(target.quantity),
                    step=1,
                )
                e_reorder = st.number_input(
                    t("med_field_reorder", lang),
                    min_value=0,
                    value=int(target.reorder_level),
                    step=1,
                )
                e_expiry = st.text_input(
                    t("med_field_expiry", lang), value=target.expiry_date
                )

            e_desc = st.text_area(
                t("med_field_desc", lang), value=target.description, height=70
            )
            save_clicked = st.form_submit_button(t("med_btn_save", lang), type="primary")

            if save_clicked and target.id is not None:
                try:
                    updated = app.inventory_service.update_medicine(
                        medicine_id=target.id,
                        name=e_name,
                        generic_name=e_generic,
                        category=e_cat_pair[0],
                        batch_number=e_batch,
                        supplier_id=supplier_map[e_supplier],
                        cost_price=e_cost,
                        unit_price=e_price,
                        quantity=int(e_qty),
                        reorder_level=int(e_reorder),
                        expiry_date=e_expiry,
                        description=e_desc,
                    )
                    WebSessionController.set_flash_success(
                        st.session_state,
                        t(
                            "med_flash_updated",
                            lang,
                            name=updated.name,
                            batch=updated.batch_number,
                        ),
                    )
                    st.rerun()
                except (ValidationError, BusinessRuleError) as exc:
                    st.error(localize_error(exc, lang))

        with st.expander(t("med_danger_zone", lang)):
            st.warning(t("med_delete_warn", lang))
            confirm_del = st.checkbox(
                t(
                    "med_confirm_delete",
                    lang,
                    name=target.name,
                    batch=target.batch_number,
                ),
                key=f"confirm_del_med_{target.id}",
            )
            if st.button(
                t("med_btn_delete", lang),
                type="secondary",
                disabled=not confirm_del,
                key=f"btn_del_med_{target.id}",
            ):
                if target.id is not None:
                    try:
                        app.inventory_service.delete_medicine(target.id)
                        WebSessionController.set_flash_success(
                            st.session_state,
                            t("med_flash_deleted", lang, name=target.name),
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(localize_error(exc, lang))
