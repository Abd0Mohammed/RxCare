"""Suppliers directory page: bilingual CRUD with referential integrity checks."""

from __future__ import annotations

import streamlit as st

from pharmacy.utils import BusinessRuleError, ValidationError
from web_app.components.theme import render_page_header
from web_app.core.i18n import localize_error, t
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_suppliers_page(app: WebAppContainer, lang: str = "ar") -> None:
    """Render Supplier CRUD directory."""
    render_page_header(t("sup_title", lang), t("sup_subtitle", lang))

    tab_list, tab_add, tab_edit = st.tabs(
        [t("sup_tab_list", lang), t("sup_tab_add", lang), t("sup_tab_edit", lang)]
    )

    with tab_list:
        search_q = st.text_input(
            t("sup_search_label", lang),
            placeholder=t("sup_search_ph", lang),
            key="sup_search_q",
        )
        suppliers = app.supplier_service.list_suppliers(search_query=search_q)
        if suppliers:
            rows = [
                {
                    t("col_id", lang): s.id,
                    t("col_supplier", lang): s.name,
                    t("col_contact", lang): s.contact_person,
                    t("col_phone", lang): s.phone,
                    t("col_email", lang): s.email,
                    t("col_address", lang): s.address,
                    t("col_linked_skus", lang): s.medicine_count,
                }
                for s in suppliers
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info(t("sup_empty_search", lang))

    with tab_add:
        with st.form("add_supplier_form", clear_on_submit=True):
            st.subheader(t("sup_add_heading", lang))
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(t("sup_field_name", lang))
                contact = st.text_input(t("sup_field_contact", lang))
                phone = st.text_input(t("sup_field_phone", lang))
            with c2:
                email = st.text_input(t("sup_field_email", lang))
                address = st.text_area(t("sup_field_address", lang), height=96)

            submitted = st.form_submit_button(t("sup_btn_create", lang), type="primary")
            if submitted:
                try:
                    created = app.supplier_service.create_supplier(
                        name=name,
                        contact_person=contact,
                        phone=phone,
                        email=email,
                        address=address,
                    )
                    WebSessionController.set_flash_success(
                        st.session_state, t("sup_flash_added", lang, name=created.name)
                    )
                    st.rerun()
                except ValidationError as exc:
                    st.error(localize_error(exc, lang))

    with tab_edit:
        suppliers = app.supplier_service.list_suppliers()
        if not suppliers:
            st.info(t("sup_none_edit", lang))
            return

        sup_map = {
            f"#{s.id} — {s.name} ({t('col_linked_skus', lang)}: {s.medicine_count})": s
            for s in suppliers
            if s.id is not None
        }
        chosen_key = st.selectbox(
            t("sup_select_edit", lang), list(sup_map.keys()), key="sup_edit_select"
        )
        target = sup_map[chosen_key]

        with st.form(f"edit_supplier_form_{target.id}"):
            st.subheader(t("sup_editing_heading", lang, name=target.name))
            c1, c2 = st.columns(2)
            with c1:
                e_name = st.text_input(t("sup_field_name", lang), value=target.name)
                e_contact = st.text_input(
                    t("sup_field_contact", lang), value=target.contact_person
                )
                e_phone = st.text_input(t("sup_field_phone", lang), value=target.phone)
            with c2:
                e_email = st.text_input(t("sup_field_email", lang), value=target.email)
                e_address = st.text_area(
                    t("sup_field_address", lang), value=target.address, height=96
                )

            saved = st.form_submit_button(t("sup_btn_update", lang), type="primary")
            if saved and target.id is not None:
                try:
                    updated = app.supplier_service.update_supplier(
                        supplier_id=target.id,
                        name=e_name,
                        contact_person=e_contact,
                        phone=e_phone,
                        email=e_email,
                        address=e_address,
                    )
                    WebSessionController.set_flash_success(
                        st.session_state,
                        t("sup_flash_updated", lang, name=updated.name),
                    )
                    st.rerun()
                except ValidationError as exc:
                    st.error(localize_error(exc, lang))

        with st.expander(t("sup_danger_zone", lang)):
            st.warning(t("sup_delete_warn", lang))
            confirm_del = st.checkbox(
                t("sup_confirm_delete", lang, name=target.name),
                key=f"confirm_del_sup_{target.id}",
            )
            if st.button(
                t("sup_btn_delete", lang),
                disabled=not confirm_del,
                key=f"btn_del_sup_{target.id}",
            ):
                if target.id is not None:
                    try:
                        app.supplier_service.delete_supplier(target.id)
                        WebSessionController.set_flash_success(
                            st.session_state,
                            t("sup_flash_deleted", lang, name=target.name),
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(localize_error(exc, lang))
