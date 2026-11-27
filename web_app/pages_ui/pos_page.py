"""Point of Sale (POS) page with cart, profit preview, expiry guard, and invoice receipt."""

from __future__ import annotations

import streamlit as st

from pharmacy.config import DEFAULT_TAX_PERCENT
from pharmacy.services.sales_service import SalesService
from pharmacy.utils import BusinessRuleError, ValidationError, format_currency
from web_app.components.theme import medicine_status_text, render_page_header
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_pos_page(app: WebAppContainer) -> None:
    """Render POS catalog search, shopping cart, profit/total preview, and checkout."""
    WebSessionController.ensure_initialized(st.session_state)

    render_page_header(
        "Point of Sale (POS)",
        "Search medicines, manage cart quantities, preview profit & taxes, and complete atomic sales.",
    )

    left_col, right_col = st.columns([1.15, 1.0])

    # ── LEFT: Medicine Search & Add to Cart ──────────────────────────────────
    with left_col:
        st.subheader("1. Medicine Catalog")
        pos_search = st.text_input(
            "Search Medicine or Batch",
            placeholder="Type medicine name, generic name, or batch #...",
            key="pos_catalog_search",
        )
        medicines = app.inventory_service.list_medicines(search_query=pos_search)

        if medicines:
            catalog_rows = [
                {
                    "ID": m.id,
                    "Medicine": m.name,
                    "Batch": m.batch_number,
                    "Price": format_currency(m.unit_price),
                    "Stock": m.quantity,
                    "Expiry": m.expiry_date,
                    "Availability": medicine_status_text(m),
                }
                for m in medicines
            ]
            st.dataframe(catalog_rows, use_container_width=True, hide_index=True)

            med_options = {
                f"#{m.id} — {m.name} ({m.batch_number}) | {format_currency(m.unit_price)} | Stock: {m.quantity} | {medicine_status_text(m)}": m
                for m in medicines
                if m.id is not None
            }
            with st.form("pos_add_to_cart_form"):
                selected_label = st.selectbox("Select Medicine Batch", list(med_options.keys()))
                qty = st.number_input("Quantity", min_value=1, value=1, step=1)
                add_btn = st.form_submit_button("Add to Cart", type="primary")
                if add_btn:
                    chosen = med_options[selected_label]
                    assert chosen.id is not None
                    try:
                        added = WebSessionController.add_to_cart(
                            st.session_state,
                            app.sales_service,
                            medicine_id=chosen.id,
                            add_quantity=int(qty),
                        )
                        st.session_state.pop(f"pos_qty_{chosen.id}", None)
                        WebSessionController.set_flash_success(
                            st.session_state,
                            f"Added {added.medicine_name} (Cart Qty: {added.quantity}).",
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(str(exc))
        else:
            st.info("No medicines found matching your query.")

    # ── RIGHT: Active Cart, Totals, Profit & Checkout ────────────────────────
    with right_col:
        st.subheader("2. Shopping Cart & Checkout")
        cart = WebSessionController.get_cart(st.session_state)

        if cart:
            cart_rows = [
                {
                    "ID": item.medicine_id,
                    "Medicine": item.medicine_name,
                    "Batch": item.batch_number,
                    "Unit Price": format_currency(item.unit_price),
                    "Qty": item.quantity,
                    "Line Total": format_currency(item.line_total),
                }
                for item in cart.values()
            ]
            st.dataframe(cart_rows, use_container_width=True, hide_index=True)

            # Inline cart item quantity adjust / remove
            c_sel, c_qty, c_upd, c_rem = st.columns([2.2, 1.0, 1.0, 1.0])
            cart_labels = {
                f"{item.medicine_name} ({item.batch_number})": item.medicine_id
                for item in cart.values()
            }
            with c_sel:
                item_label = st.selectbox(
                    "Edit Cart Line", list(cart_labels.keys()), key="pos_edit_line"
                )
            edit_med_id = cart_labels[item_label]
            with c_qty:
                new_qty = st.number_input(
                    "New Qty",
                    min_value=0,
                    value=cart[edit_med_id].quantity,
                    step=1,
                    key=f"pos_qty_{edit_med_id}",
                )
            with c_upd:
                st.write("")
                st.write("")
                if st.button("Update", key="pos_btn_update"):
                    try:
                        WebSessionController.update_cart_quantity(
                            st.session_state, app.sales_service, edit_med_id, int(new_qty)
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(str(exc))
            with c_rem:
                st.write("")
                st.write("")
                if st.button("Remove", key="pos_btn_remove"):
                    WebSessionController.remove_from_cart(st.session_state, edit_med_id)
                    st.session_state.pop(f"pos_qty_{edit_med_id}", None)
                    st.rerun()

            if st.button("Clear Entire Cart", key="pos_clear_cart"):
                for mid in list(cart.keys()):
                    st.session_state.pop(f"pos_qty_{mid}", None)
                WebSessionController.clear_cart(st.session_state)
                st.rerun()
        else:
            st.info("Your cart is empty. Add valid non-expired medicines from the catalog.")

        # Billing & Profit Preview
        items_list = list(cart.values())
        with st.form("pos_checkout_form"):
            b1, b2 = st.columns(2)
            with b1:
                customer_name = st.text_input("Customer Name", value="Walk-in Customer")
                discount_pct = st.number_input(
                    "Discount (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0
                )
                payment_method = st.selectbox(
                    "Payment Method", list(SalesService.VALID_PAYMENT_METHODS)
                )
            with b2:
                customer_phone = st.text_input("Customer Phone", value="")
                tax_pct = st.number_input(
                    "Tax (%)", min_value=0.0, max_value=100.0, value=float(DEFAULT_TAX_PERCENT), step=0.5
                )
                amount_paid_raw = st.text_input(
                    "Amount Tendered (blank = exact total)", value=""
                )

            notes = st.text_input("Invoice Notes (optional)", value="")

            try:
                totals = app.sales_service.calculate_totals(
                    items=items_list,
                    discount_percent=discount_pct,
                    tax_percent=tax_pct,
                )
                profit_info = app.analytics_service.calculate_cart_profit(
                    items=items_list, discount_percent=discount_pct
                )
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Subtotal", format_currency(totals.subtotal))
                m2.metric("Discount", f"-{format_currency(totals.discount_amount)}")
                m3.metric("Tax", format_currency(totals.tax_amount))
                m4.metric("Grand Total", format_currency(totals.total_amount))
                st.caption(
                    f"Estimated Cost: {format_currency(profit_info['cost'])} | "
                    f"Estimated Net Profit: {format_currency(profit_info['net_profit'])}"
                )
            except ValidationError as exc:
                st.error(str(exc))

            complete_btn = st.form_submit_button(
                "Complete Sale & Generate Invoice",
                type="primary",
                disabled=len(items_list) == 0,
            )

            if complete_btn:
                paid_arg = amount_paid_raw.strip() if amount_paid_raw.strip() else None
                try:
                    sale, created_new = WebSessionController.complete_sale_idempotent(
                        session_state=st.session_state,
                        sales_service=app.sales_service,
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        discount_percent=discount_pct,
                        tax_percent=tax_pct,
                        amount_paid=paid_arg,
                        payment_method=payment_method,
                        notes=notes,
                    )
                    if created_new:
                        WebSessionController.set_flash_success(
                            st.session_state,
                            f"Sale completed! Invoice {sale.invoice_number} — Total {format_currency(sale.total_amount)}",
                        )
                    st.rerun()
                except (ValidationError, BusinessRuleError) as exc:
                    st.error(f"Checkout failed: {exc}")

    # ── Last Completed Invoice Summary ────────────────────────────────────────
    last_sale = st.session_state.get(WebSessionController.LAST_SALE_KEY)
    if last_sale is not None:
        st.markdown("---")
        st.subheader(f"Latest Invoice Summary — {last_sale.invoice_number}")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Customer", last_sale.customer_name)
        s2.metric("Payment", last_sale.payment_method)
        s3.metric("Grand Total", format_currency(last_sale.total_amount))
        s4.metric("Change Due", format_currency(last_sale.change_due))

        receipt_lines = [
            {
                "Medicine": item.medicine_name,
                "Batch #": item.batch_number,
                "Qty": item.quantity,
                "Unit Price": format_currency(item.unit_price),
                "Line Total": format_currency(item.line_total),
            }
            for item in last_sale.items
        ]
        st.dataframe(receipt_lines, use_container_width=True, hide_index=True)
