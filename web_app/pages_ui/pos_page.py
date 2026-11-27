"""Point of Sale (POS) page: bilingual catalog, cart, profit preview, and atomic checkout."""

from __future__ import annotations

import streamlit as st

from pharmacy.config import DEFAULT_TAX_PERCENT
from pharmacy.utils import BusinessRuleError, ValidationError, format_currency
from web_app.components.theme import medicine_status_text, render_page_header
from web_app.core.i18n import (
    PAYMENT_KEYS,
    localize_error,
    t,
    translate_payment_method,
)
from web_app.core.web_services import WebAppContainer, WebSessionController


def render_pos_page(app: WebAppContainer, lang: str = "ar") -> None:
    """Render POS catalog search, shopping cart, profit/total preview, and checkout."""
    WebSessionController.ensure_initialized(st.session_state)

    render_page_header(t("pos_title", lang), t("pos_subtitle", lang))

    left_col, right_col = st.columns([1.15, 1.0])

    # ── LEFT: Medicine Search & Add to Cart ──────────────────────────────────
    with left_col:
        st.subheader(t("pos_catalog_heading", lang))
        pos_search = st.text_input(
            t("pos_search_label", lang),
            placeholder=t("pos_search_ph", lang),
            key="pos_catalog_search",
        )
        medicines = app.inventory_service.list_medicines(search_query=pos_search)

        if medicines:
            catalog_rows = [
                {
                    t("col_id", lang): m.id,
                    t("col_medicine", lang): m.name,
                    t("col_batch", lang): m.batch_number,
                    t("col_price", lang): format_currency(m.unit_price),
                    t("col_qty", lang): m.quantity,
                    t("col_expiry", lang): m.expiry_date,
                    t("col_availability", lang): medicine_status_text(m, lang=lang),
                }
                for m in medicines
            ]
            st.dataframe(catalog_rows, use_container_width=True, hide_index=True)

            med_options = {
                f"#{m.id} — {m.name} ({m.batch_number}) | {format_currency(m.unit_price)} | {t('col_qty', lang)}: {m.quantity} | {medicine_status_text(m, lang=lang)}": m
                for m in medicines
                if m.id is not None
            }
            with st.form("pos_add_to_cart_form"):
                selected_label = st.selectbox(
                    t("pos_select_batch", lang), list(med_options.keys())
                )
                qty = st.number_input(t("pos_qty_label", lang), min_value=1, value=1, step=1)
                add_btn = st.form_submit_button(t("pos_btn_add_cart", lang), type="primary")
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
                            t(
                                "pos_flash_added",
                                lang,
                                name=added.medicine_name,
                                qty=added.quantity,
                            ),
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(localize_error(exc, lang))
        else:
            st.info(t("pos_empty_catalog", lang))

    # ── RIGHT: Active Cart, Totals, Profit & Checkout ────────────────────────
    with right_col:
        st.subheader(t("pos_cart_heading", lang))
        cart = WebSessionController.get_cart(st.session_state)

        if cart:
            cart_rows = [
                {
                    t("col_id", lang): item.medicine_id,
                    t("col_medicine", lang): item.medicine_name,
                    t("col_batch", lang): item.batch_number,
                    t("col_unit_price", lang): format_currency(item.unit_price),
                    t("col_qty", lang): item.quantity,
                    t("col_line_total", lang): format_currency(item.line_total),
                }
                for item in cart.values()
            ]
            st.dataframe(cart_rows, use_container_width=True, hide_index=True)

            c_sel, c_qty, c_upd, c_rem = st.columns([2.2, 1.0, 1.0, 1.0])
            cart_labels = {
                f"{item.medicine_name} ({item.batch_number})": item.medicine_id
                for item in cart.values()
            }
            with c_sel:
                item_label = st.selectbox(
                    t("pos_edit_line", lang), list(cart_labels.keys()), key="pos_edit_line"
                )
            edit_med_id = cart_labels[item_label]
            with c_qty:
                new_qty = st.number_input(
                    t("pos_new_qty", lang),
                    min_value=0,
                    value=cart[edit_med_id].quantity,
                    step=1,
                    key=f"pos_qty_{edit_med_id}",
                )
            with c_upd:
                st.write("")
                st.write("")
                if st.button(t("pos_btn_update", lang), key="pos_btn_update"):
                    try:
                        WebSessionController.update_cart_quantity(
                            st.session_state, app.sales_service, edit_med_id, int(new_qty)
                        )
                        st.rerun()
                    except (ValidationError, BusinessRuleError) as exc:
                        st.error(localize_error(exc, lang))
            with c_rem:
                st.write("")
                st.write("")
                if st.button(t("pos_btn_remove", lang), key="pos_btn_remove"):
                    WebSessionController.remove_from_cart(st.session_state, edit_med_id)
                    st.session_state.pop(f"pos_qty_{edit_med_id}", None)
                    st.rerun()

            if st.button(t("pos_btn_clear", lang), key="pos_clear_cart"):
                for mid in list(cart.keys()):
                    st.session_state.pop(f"pos_qty_{mid}", None)
                WebSessionController.clear_cart(st.session_state)
                st.rerun()
        else:
            st.info(t("pos_empty_cart", lang))

        items_list = list(cart.values())
        payment_choices = [(canonical, t(key, lang)) for canonical, key in PAYMENT_KEYS]

        with st.form("pos_checkout_form"):
            b1, b2 = st.columns(2)
            with b1:
                customer_name = st.text_input(
                    t("pos_customer_name", lang), value=t("walk_in_customer", lang)
                )
                discount_pct = st.number_input(
                    t("pos_discount_pct", lang),
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=1.0,
                )
                payment_pair = st.selectbox(
                    t("pos_payment_method", lang),
                    payment_choices,
                    format_func=lambda item: item[1],
                )
            with b2:
                customer_phone = st.text_input(t("pos_customer_phone", lang), value="")
                tax_pct = st.number_input(
                    t("pos_tax_pct", lang),
                    min_value=0.0,
                    max_value=100.0,
                    value=float(DEFAULT_TAX_PERCENT),
                    step=0.5,
                )
                amount_paid_raw = st.text_input(t("pos_amount_paid", lang), value="")

            notes = st.text_input(t("pos_notes", lang), value="")

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
                m1.metric(t("col_subtotal", lang), format_currency(totals.subtotal))
                m2.metric(
                    t("col_discount", lang), f"-{format_currency(totals.discount_amount)}"
                )
                m3.metric(t("col_tax", lang), format_currency(totals.tax_amount))
                m4.metric(t("col_grand_total", lang), format_currency(totals.total_amount))
                st.caption(
                    t(
                        "pos_est_caption",
                        lang,
                        cost=format_currency(profit_info["cost"]),
                        profit=format_currency(profit_info["net_profit"]),
                    )
                )
            except ValidationError as exc:
                st.error(localize_error(exc, lang))

            complete_btn = st.form_submit_button(
                t("pos_btn_checkout", lang),
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
                        payment_method=payment_pair[0],
                        notes=notes,
                    )
                    if created_new:
                        WebSessionController.set_flash_success(
                            st.session_state,
                            t(
                                "pos_flash_sale",
                                lang,
                                invoice=sale.invoice_number,
                                total=format_currency(sale.total_amount),
                            ),
                        )
                    st.rerun()
                except (ValidationError, BusinessRuleError) as exc:
                    st.error(
                        t("pos_checkout_failed", lang, err=localize_error(exc, lang))
                    )

    # ── Last Completed Invoice Summary ────────────────────────────────────────
    last_sale = st.session_state.get(WebSessionController.LAST_SALE_KEY)
    if last_sale is not None:
        st.markdown("---")
        st.subheader(t("pos_latest_invoice", lang, invoice=last_sale.invoice_number))
        s1, s2, s3, s4 = st.columns(4)
        s1.metric(t("col_customer", lang), last_sale.customer_name)
        s2.metric(
            t("col_payment", lang),
            translate_payment_method(last_sale.payment_method, lang),
        )
        s3.metric(t("col_grand_total", lang), format_currency(last_sale.total_amount))
        s4.metric(t("pos_change_due", lang), format_currency(last_sale.change_due))

        receipt_lines = [
            {
                t("col_medicine", lang): item.medicine_name,
                t("col_batch", lang): item.batch_number,
                t("col_qty", lang): item.quantity,
                t("col_unit_price", lang): format_currency(item.unit_price),
                t("col_line_total", lang): format_currency(item.line_total),
            }
            for item in last_sale.items
        ]
        st.dataframe(receipt_lines, use_container_width=True, hide_index=True)
