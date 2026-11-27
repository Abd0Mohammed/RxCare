"""Suppliers directory page with full CRUD and referential integrity checks."""

from __future__ import annotations

import streamlit as st

from pharmacy.utils import BusinessRuleError, ValidationError
from web_app.components.theme import render_page_header
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_suppliers_page(app: WebAppContainer) -> None:
    """Render Supplier CRUD directory."""
    render_page_header(
        "Suppliers",
        "Manage wholesale pharmaceutical vendors, contact details, and linked SKU counts.",
    )

    tab_list, tab_add, tab_edit = st.tabs(
        ["Supplier Directory", "Add Supplier", "Edit / Delete Supplier"]
    )

    with tab_list:
        search_q = st.text_input(
            "Search Suppliers",
            placeholder="Name, contact person, phone, or email...",
            key="sup_search_q",
        )
        suppliers = app.supplier_service.list_suppliers(search_query=search_q)
        if suppliers:
            rows = [
                {
                    "ID": s.id,
                    "Supplier Name": s.name,
                    "Contact Person": s.contact_person,
                    "Phone": s.phone,
                    "Email": s.email,
                    "Address": s.address,
                    "Linked SKUs": s.medicine_count,
                }
                for s in suppliers
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No suppliers match your search.")

    with tab_add:
        with st.form("add_supplier_form", clear_on_submit=True):
            st.subheader("Add New Supplier")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Supplier Name *")
                contact = st.text_input("Contact Person")
                phone = st.text_input("Phone Number")
            with c2:
                email = st.text_input("Email Address")
                address = st.text_area("Street Address", height=96)

            submitted = st.form_submit_button("Create Supplier", type="primary")
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
                        st.session_state, f"Supplier '{created.name}' added."
                    )
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))

    with tab_edit:
        suppliers = app.supplier_service.list_suppliers()
        if not suppliers:
            st.info("No suppliers available to edit.")
            return

        sup_map = {
            f"#{s.id} — {s.name} ({s.medicine_count} linked SKUs)": s
            for s in suppliers
            if s.id is not None
        }
        chosen_key = st.selectbox(
            "Select Supplier", list(sup_map.keys()), key="sup_edit_select"
        )
        target = sup_map[chosen_key]

        with st.form(f"edit_supplier_form_{target.id}"):
            st.subheader(f"Editing {target.name}")
            c1, c2 = st.columns(2)
            with c1:
                e_name = st.text_input("Supplier Name *", value=target.name)
                e_contact = st.text_input("Contact Person", value=target.contact_person)
                e_phone = st.text_input("Phone Number", value=target.phone)
            with c2:
                e_email = st.text_input("Email Address", value=target.email)
                e_address = st.text_area("Street Address", value=target.address, height=96)

            saved = st.form_submit_button("Update Supplier", type="primary")
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
                        st.session_state, f"Updated supplier '{updated.name}'."
                    )
                    st.rerun()
                except ValidationError as exc:
                    st.error(str(exc))

        with st.expander("Danger Zone — Delete Supplier"):
            st.warning(
                "Suppliers linked to existing medicine batches cannot be deleted until medicines are reassigned or removed."
            )
            confirm_del = st.checkbox(
                f"I confirm deleting supplier '{target.name}'",
                key=f"confirm_del_sup_{target.id}",
            )
            if st.button(
                "Delete Supplier",
                disabled=not confirm_del,
                key=f"btn_del_sup_{target.id}",
            ):
                if target.id is not None:
                    try:
                        app.supplier_service.delete_supplier(target.id)
                        WebSessionController.set_flash_success(
                            st.session_state, f"Deleted supplier '{target.name}'."
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(str(exc))
