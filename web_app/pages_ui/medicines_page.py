"""Medicine Management page: CRUD, search, category filter, and detail inspection."""

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


def render_medicines_page(app: WebAppContainer) -> None:
    """Render medicine catalog management with search, category filter, and CRUD tabs."""
    render_page_header(
        "Medicine Management",
        "Search catalog batches, filter by therapeutic category, inspect details, and manage SKUs.",
    )

    tab_catalog, tab_add, tab_edit = st.tabs(
        ["Catalog & Details", "Add Medicine", "Edit / Delete Medicine"]
    )

    # ── TAB 1: Catalog Search, Category Filter & Detail Viewer ────────────────
    with tab_catalog:
        categories = ["All Categories"] + sorted(
            set(DEFAULT_CATEGORIES)
            | set(app.analytics_service.list_categories(app.inventory_service))
        )
        f1, f2, f3 = st.columns([2, 1.3, 1.3])
        with f1:
            search_q = st.text_input(
                "Search Medicines",
                placeholder="Name, generic name, batch #, or supplier...",
                key="med_search_q",
            )
        with f2:
            selected_cat = st.selectbox("Category", categories, key="med_cat_filter")
        with f3:
            status_opt = st.selectbox(
                "Availability",
                [
                    ("All", "all"),
                    ("Available for Sale", "available_for_sale"),
                    ("Low Stock", "low_stock"),
                    ("Expiring Soon", "expiring_soon"),
                    ("Expired", "expired"),
                ],
                format_func=lambda item: item[0],
                key="med_status_filter",
            )

        medicines = app.analytics_service.filter_medicines(
            app.inventory_service,
            search_query=search_q,
            status_filter=status_opt[1],
            category=selected_cat,
        )

        if medicines:
            rows = [
                {
                    "ID": m.id,
                    "Name": m.name,
                    "Generic": m.generic_name,
                    "Category": m.category,
                    "Batch #": m.batch_number,
                    "Supplier": m.supplier_name,
                    "Cost": format_currency(m.cost_price),
                    "Price": format_currency(m.unit_price),
                    "Qty": m.quantity,
                    "Expiry": m.expiry_date,
                    "Status": medicine_status_text(m),
                }
                for m in medicines
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            st.subheader("Medicine Batch Details")
            med_lookup = {
                f"#{m.id} — {m.name} (Batch {m.batch_number})": m
                for m in medicines
                if m.id is not None
            }
            chosen_label = st.selectbox(
                "Inspect Batch", list(med_lookup.keys()), key="med_inspect_select"
            )
            chosen = med_lookup[chosen_label]
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Selling Price", format_currency(chosen.unit_price))
            d2.metric("Cost Price", format_currency(chosen.cost_price))
            d3.metric(
                "Unit Margin",
                format_currency(round(chosen.unit_price - chosen.cost_price, 2)),
            )
            d4.metric("Stock / Reorder", f"{chosen.quantity} / {chosen.reorder_level}")
            st.caption(
                f"Generic: {chosen.generic_name or 'N/A'} | Category: {chosen.category} | "
                f"Supplier: {chosen.supplier_name} | Expiry: {chosen.expiry_date} ({medicine_status_text(chosen)})"
            )
            if chosen.description:
                st.info(chosen.description)
        else:
            st.info("No medicines match the current search or category filters.")

    # ── TAB 2: Add Medicine ───────────────────────────────────────────────────
    with tab_add:
        suppliers = app.supplier_service.list_suppliers()
        supplier_map: dict[str, int | None] = {"(Unassigned)": None}
        for sup in suppliers:
            if sup.id is not None:
                supplier_map[sup.name] = sup.id

        with st.form("add_medicine_form", clear_on_submit=True):
            st.subheader("Register New Medicine Batch")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Medicine Name *")
                generic = st.text_input("Generic Name")
                category = st.selectbox("Category", DEFAULT_CATEGORIES, index=9)
                batch = st.text_input("Batch Number *")
                supplier_label = st.selectbox("Supplier", list(supplier_map.keys()))
            with c2:
                cost_price = st.number_input("Cost Price ($)", min_value=0.0, step=0.25, format="%.2f")
                unit_price = st.number_input("Unit Selling Price ($) *", min_value=0.01, value=5.00, step=0.25, format="%.2f")
                quantity = st.number_input("Initial Stock Quantity *", min_value=0, value=20, step=1)
                reorder_level = st.number_input("Reorder Alert Level", min_value=0, value=DEFAULT_LOW_STOCK_THRESHOLD, step=1)
                expiry_date = st.text_input("Expiry Date (YYYY-MM-DD) *", value=today_iso())

            description = st.text_area("Description / Storage Notes", height=70)
            submitted = st.form_submit_button("Add Medicine Batch", type="primary")

            if submitted:
                try:
                    created = app.inventory_service.create_medicine(
                        name=name,
                        generic_name=generic,
                        category=category,
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
                        f"Added '{created.name}' (Batch {created.batch_number}) to inventory.",
                    )
                    st.rerun()
                except (ValidationError, BusinessRuleError) as exc:
                    st.error(str(exc))

    # ── TAB 3: Edit or Delete Medicine ────────────────────────────────────────
    with tab_edit:
        all_meds = app.inventory_service.list_medicines()
        if not all_meds:
            st.info("No medicines available to edit or delete.")
            return

        edit_map = {
            f"#{m.id} — {m.name} ({m.batch_number})": m
            for m in all_meds
            if m.id is not None
        }
        selected_key = st.selectbox(
            "Select Medicine Batch to Modify", list(edit_map.keys()), key="med_edit_select"
        )
        target = edit_map[selected_key]

        suppliers = app.supplier_service.list_suppliers()
        supplier_map = {"(Unassigned)": None}
        default_sup_label = "(Unassigned)"
        for sup in suppliers:
            if sup.id is not None:
                supplier_map[sup.name] = sup.id
                if sup.id == target.supplier_id:
                    default_sup_label = sup.name

        cat_options = list(dict.fromkeys(DEFAULT_CATEGORIES + [target.category]))

        with st.form(f"edit_medicine_form_{target.id}"):
            st.subheader(f"Editing {target.name} ({target.batch_number})")
            c1, c2 = st.columns(2)
            with c1:
                e_name = st.text_input("Medicine Name *", value=target.name)
                e_generic = st.text_input("Generic Name", value=target.generic_name)
                e_category = st.selectbox(
                    "Category", cat_options, index=cat_options.index(target.category)
                )
                e_batch = st.text_input("Batch Number *", value=target.batch_number)
                sup_keys = list(supplier_map.keys())
                e_supplier = st.selectbox(
                    "Supplier", sup_keys, index=sup_keys.index(default_sup_label)
                )
            with c2:
                e_cost = st.number_input(
                    "Cost Price ($)", min_value=0.0, value=float(target.cost_price), step=0.25, format="%.2f"
                )
                e_price = st.number_input(
                    "Unit Selling Price ($) *",
                    min_value=0.01,
                    value=max(0.01, float(target.unit_price)),
                    step=0.25,
                    format="%.2f",
                )
                e_qty = st.number_input(
                    "Stock Quantity *", min_value=0, value=int(target.quantity), step=1
                )
                e_reorder = st.number_input(
                    "Reorder Alert Level", min_value=0, value=int(target.reorder_level), step=1
                )
                e_expiry = st.text_input("Expiry Date (YYYY-MM-DD) *", value=target.expiry_date)

            e_desc = st.text_area("Description / Notes", value=target.description, height=70)
            save_clicked = st.form_submit_button("Save Changes", type="primary")

            if save_clicked and target.id is not None:
                try:
                    updated = app.inventory_service.update_medicine(
                        medicine_id=target.id,
                        name=e_name,
                        generic_name=e_generic,
                        category=e_category,
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
                        f"Updated '{updated.name}' (Batch {updated.batch_number}).",
                    )
                    st.rerun()
                except (ValidationError, BusinessRuleError) as exc:
                    st.error(str(exc))

        with st.expander("Danger Zone — Delete Medicine Batch"):
            st.warning(
                "Deleting removes the batch permanently. Batches with historical sales cannot be deleted."
            )
            confirm_del = st.checkbox(
                f"I confirm deleting '{target.name}' (Batch {target.batch_number})",
                key=f"confirm_del_med_{target.id}",
            )
            if st.button(
                "Delete Medicine Batch",
                type="secondary",
                disabled=not confirm_del,
                key=f"btn_del_med_{target.id}",
            ):
                if target.id is not None:
                    try:
                        app.inventory_service.delete_medicine(target.id)
                        WebSessionController.set_flash_success(
                            st.session_state, f"Deleted '{target.name}'."
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(str(exc))
