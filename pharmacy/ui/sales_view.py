"""Point of Sale (POS) billing view with strict expiry checks and receipt modal."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from pharmacy.config import COLORS, DEFAULT_TAX_PERCENT, FONTS
from pharmacy.models.entities import CartItem, Medicine, Sale
from pharmacy.services.inventory_service import InventoryService
from pharmacy.services.sales_service import SalesService
from pharmacy.ui.styles import center_toplevel
from pharmacy.utils import (
    BusinessRuleError,
    ValidationError,
    expiry_status_label,
    format_currency,
    parse_positive_int,
)


class ReceiptDialog(tk.Toplevel):
    """Printable / viewable receipt modal shown after completed checkout."""

    def __init__(self, parent: tk.Misc, sale: Sale) -> None:
        super().__init__(parent)
        self.sale = sale
        self.title(f"Sale Receipt - {sale.invoice_number}")
        self.configure(bg=COLORS["bg_surface"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        container = tk.Frame(self, bg=COLORS["bg_surface"], padx=18, pady=16)
        container.pack(fill="both", expand=True)

        text_box = tk.Text(
            container,
            width=54,
            height=24,
            font=FONTS["mono"],
            bg="#FAFAFA",
            fg=COLORS["text_primary"],
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=10,
        )
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", self._format_receipt(sale))
        text_box.configure(state="disabled")

        btn_row = tk.Frame(container, bg=COLORS["bg_surface"])
        btn_row.pack(fill="x", pady=(12, 0))
        ttk.Button(
            btn_row, text="Close", style="Primary.TButton", command=self.destroy
        ).pack(side="right")

        center_toplevel(self, parent, 520, 500)
        self.bind("<Escape>", lambda _e: self.destroy())

    @staticmethod
    def _format_receipt(sale: Sale) -> str:
        lines = [
            "================================================",
            "         RXCARE PHARMACY MANAGEMENT POS         ",
            "================================================",
            f"Invoice   : {sale.invoice_number}",
            f"Date      : {sale.sale_date}",
            f"Customer  : {sale.customer_name}",
        ]
        if sale.customer_phone:
            lines.append(f"Phone     : {sale.customer_phone}")
        lines.append(f"Payment   : {sale.payment_method}")
        lines.append("------------------------------------------------")
        lines.append(f"{'Item':<24} {'Qty':>4} {'Price':>8} {'Total':>9}")
        lines.append("------------------------------------------------")
        for item in sale.items:
            name = item.medicine_name[:24]
            lines.append(
                f"{name:<24} {item.quantity:>4} {item.unit_price:>8.2f} {item.line_total:>9.2f}"
            )
        lines.append("------------------------------------------------")
        lines.append(f"{'Subtotal:':<36} {format_currency(sale.subtotal):>11}")
        lines.append(
            f"{f'Discount ({sale.discount_percent:.1f}%):':<36} -{format_currency(sale.discount_amount):>10}"
        )
        lines.append(
            f"{f'Tax ({sale.tax_percent:.1f}%):':<36} {format_currency(sale.tax_amount):>11}"
        )
        lines.append(f"{'GRAND TOTAL:':<36} {format_currency(sale.total_amount):>11}")
        lines.append(f"{'Amount Paid:':<36} {format_currency(sale.amount_paid):>11}")
        lines.append(f"{'Change Due:':<36} {format_currency(sale.change_due):>11}")
        lines.append("================================================")
        lines.append("        Thank you for choosing RxCare!          ")
        return "\n".join(lines)


class SalesView(ttk.Frame):
    """Split POS screen: Medicine Picker (left) and Active Cart & Checkout (right)."""

    def __init__(
        self,
        parent: tk.Misc,
        inventory_service: InventoryService,
        sales_service: SalesService,
        on_data_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, style="App.TFrame")
        self.inventory_service = inventory_service
        self.sales_service = sales_service
        self.on_data_changed = on_data_changed

        self.search_var = tk.StringVar()
        self.add_qty_var = tk.StringVar(value="1")
        self.customer_name_var = tk.StringVar(value="Walk-in Customer")
        self.customer_phone_var = tk.StringVar()
        self.payment_method_var = tk.StringVar(value="Cash")
        self.discount_var = tk.StringVar(value="0")
        self.tax_var = tk.StringVar(value=f"{DEFAULT_TAX_PERCENT:.1f}")
        self.amount_paid_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        self.subtotal_lbl_var = tk.StringVar(value=format_currency(0))
        self.discount_lbl_var = tk.StringVar(value=format_currency(0))
        self.tax_lbl_var = tk.StringVar(value=format_currency(0))
        self.total_lbl_var = tk.StringVar(value=format_currency(0))
        self.change_lbl_var = tk.StringVar(value=format_currency(0))

        self._catalog_by_id: dict[int, Medicine] = {}
        self._cart: dict[int, CartItem] = {}

        self._build_ui()

        for var in (self.discount_var, self.tax_var, self.amount_paid_var):
            var.trace_add("write", lambda *_args: self._recalculate_summary())

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Sales & Point of Sale (POS)", style="Title.TLabel").pack(
            side="left"
        )
        ttk.Label(
            header,
            text="Expired and out-of-stock batches are automatically blocked from checkout.",
            style="AppMuted.TLabel",
        ).pack(side="right", pady=(6, 0))

        split = ttk.Frame(self, style="App.TFrame")
        split.pack(fill="both", expand=True)
        split.columnconfigure(0, weight=11, uniform="pos")
        split.columnconfigure(1, weight=10, uniform="pos")
        split.rowconfigure(0, weight=1)

        # LEFT PANEL: Medicine Catalog
        left_card = tk.Frame(
            split,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            left_card,
            text="1. Select Medicine Batch",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["subtitle"],
        ).pack(anchor="w", pady=(0, 8))

        search_row = tk.Frame(left_card, bg=COLORS["bg_surface"])
        search_row.pack(fill="x", pady=(0, 8))

        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        search_entry.bind("<Return>", lambda _e: self.refresh())

        ttk.Button(
            search_row, text="Search", style="Secondary.TButton", command=self.refresh
        ).pack(side="left")

        cat_frame = tk.Frame(left_card, bg=COLORS["bg_surface"])
        cat_frame.pack(fill="both", expand=True)

        cat_cols = ("name", "batch", "price", "stock", "expiry", "status")
        self.catalog_tree = ttk.Treeview(
            cat_frame, columns=cat_cols, show="headings", selectmode="browse"
        )
        for col_id, label, width, anchor in [
            ("name", "Medicine", 170, "w"),
            ("batch", "Batch", 95, "w"),
            ("price", "Price", 70, "e"),
            ("stock", "Stock", 55, "e"),
            ("expiry", "Expiry", 88, "center"),
            ("status", "Availability", 100, "center"),
        ]:
            self.catalog_tree.heading(col_id, text=label)
            self.catalog_tree.column(col_id, width=width, anchor=anchor)

        self.catalog_tree.tag_configure("expired", background=COLORS["danger_bg"])
        self.catalog_tree.tag_configure("warning", background=COLORS["warning_bg"])
        self.catalog_tree.bind("<Double-1>", lambda _e: self._add_selected_to_cart())

        cat_sb = ttk.Scrollbar(cat_frame, orient="vertical", command=self.catalog_tree.yview)
        self.catalog_tree.configure(yscrollcommand=cat_sb.set)
        self.catalog_tree.pack(side="left", fill="both", expand=True)
        cat_sb.pack(side="right", fill="y")

        add_bar = tk.Frame(left_card, bg=COLORS["bg_surface"])
        add_bar.pack(fill="x", pady=(10, 0))
        tk.Label(
            add_bar,
            text="Qty:",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).pack(side="left", padx=(0, 6))
        ttk.Entry(add_bar, textvariable=self.add_qty_var, width=8).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(
            add_bar,
            text="Add to Cart ->",
            style="Primary.TButton",
            command=self._add_selected_to_cart,
        ).pack(side="left")

        # RIGHT PANEL: Cart & Checkout
        right_card = tk.Frame(
            split,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        cart_top = tk.Frame(right_card, bg=COLORS["bg_surface"])
        cart_top.pack(fill="x", pady=(0, 8))
        tk.Label(
            cart_top,
            text="2. Active Cart & Billing",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["subtitle"],
        ).pack(side="left")
        ttk.Button(
            cart_top, text="Remove Item", style="Secondary.TButton", command=self._remove_cart_item
        ).pack(side="right", padx=(6, 0))
        ttk.Button(
            cart_top, text="Clear Cart", style="Secondary.TButton", command=self._clear_cart
        ).pack(side="right")

        cart_table_frame = tk.Frame(right_card, bg=COLORS["bg_surface"])
        cart_table_frame.pack(fill="both", expand=True)

        cart_cols = ("name", "batch", "qty", "unit_price", "line_total")
        self.cart_tree = ttk.Treeview(
            cart_table_frame, columns=cart_cols, show="headings", height=7, selectmode="browse"
        )
        for col_id, label, width, anchor in [
            ("name", "Medicine", 170, "w"),
            ("batch", "Batch", 95, "w"),
            ("qty", "Qty", 50, "e"),
            ("unit_price", "Unit Price", 80, "e"),
            ("line_total", "Line Total", 85, "e"),
        ]:
            self.cart_tree.heading(col_id, text=label)
            self.cart_tree.column(col_id, width=width, anchor=anchor)

        cart_sb = ttk.Scrollbar(
            cart_table_frame, orient="vertical", command=self.cart_tree.yview
        )
        self.cart_tree.configure(yscrollcommand=cart_sb.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        cart_sb.pack(side="right", fill="y")

        # Customer & Billing Inputs
        form = tk.Frame(right_card, bg=COLORS["bg_surface"], pady=8)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        tk.Label(form, text="Customer:", bg=COLORS["bg_surface"], font=FONTS["small"]).grid(
            row=0, column=0, sticky="w", pady=3, padx=(0, 6)
        )
        ttk.Entry(form, textvariable=self.customer_name_var).grid(
            row=0, column=1, sticky="ew", pady=3, padx=(0, 12)
        )
        tk.Label(form, text="Phone:", bg=COLORS["bg_surface"], font=FONTS["small"]).grid(
            row=0, column=2, sticky="w", pady=3, padx=(0, 6)
        )
        ttk.Entry(form, textvariable=self.customer_phone_var).grid(
            row=0, column=3, sticky="ew", pady=3
        )

        tk.Label(form, text="Discount %:", bg=COLORS["bg_surface"], font=FONTS["small"]).grid(
            row=1, column=0, sticky="w", pady=3, padx=(0, 6)
        )
        ttk.Entry(form, textvariable=self.discount_var).grid(
            row=1, column=1, sticky="ew", pady=3, padx=(0, 12)
        )
        tk.Label(form, text="Tax %:", bg=COLORS["bg_surface"], font=FONTS["small"]).grid(
            row=1, column=2, sticky="w", pady=3, padx=(0, 6)
        )
        ttk.Entry(form, textvariable=self.tax_var).grid(
            row=1, column=3, sticky="ew", pady=3
        )

        tk.Label(form, text="Payment:", bg=COLORS["bg_surface"], font=FONTS["small"]).grid(
            row=2, column=0, sticky="w", pady=3, padx=(0, 6)
        )
        ttk.Combobox(
            form,
            textvariable=self.payment_method_var,
            values=list(SalesService.VALID_PAYMENT_METHODS),
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", pady=3, padx=(0, 12))
        tk.Label(form, text="Amount Paid:", bg=COLORS["bg_surface"], font=FONTS["small"]).grid(
            row=2, column=2, sticky="w", pady=3, padx=(0, 6)
        )
        ttk.Entry(form, textvariable=self.amount_paid_var).grid(
            row=2, column=3, sticky="ew", pady=3
        )

        # Totals Summary Box
        summary = tk.Frame(
            right_card,
            bg="#F8FAFC",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        summary.pack(fill="x", pady=(4, 10))
        summary.columnconfigure(1, weight=1)
        summary.columnconfigure(3, weight=1)

        tk.Label(summary, text="Subtotal:", bg="#F8FAFC", font=FONTS["body"]).grid(
            row=0, column=0, sticky="w"
        )
        tk.Label(
            summary, textvariable=self.subtotal_lbl_var, bg="#F8FAFC", font=FONTS["body_bold"]
        ).grid(row=0, column=1, sticky="e", padx=(0, 16))

        tk.Label(summary, text="Discount:", bg="#F8FAFC", font=FONTS["body"]).grid(
            row=0, column=2, sticky="w"
        )
        tk.Label(
            summary, textvariable=self.discount_lbl_var, bg="#F8FAFC", font=FONTS["body_bold"]
        ).grid(row=0, column=3, sticky="e")

        tk.Label(summary, text="Tax:", bg="#F8FAFC", font=FONTS["body"]).grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        tk.Label(
            summary, textvariable=self.tax_lbl_var, bg="#F8FAFC", font=FONTS["body_bold"]
        ).grid(row=1, column=1, sticky="e", padx=(0, 16), pady=(2, 0))

        tk.Label(summary, text="Change Due:", bg="#F8FAFC", font=FONTS["body"]).grid(
            row=1, column=2, sticky="w", pady=(2, 0)
        )
        tk.Label(
            summary, textvariable=self.change_lbl_var, bg="#F8FAFC", font=FONTS["body_bold"]
        ).grid(row=1, column=3, sticky="e", pady=(2, 0))

        tk.Label(
            summary,
            text="GRAND TOTAL:",
            bg="#F8FAFC",
            fg=COLORS["primary"],
            font=FONTS["subtitle"],
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        tk.Label(
            summary,
            textvariable=self.total_lbl_var,
            bg="#F8FAFC",
            fg=COLORS["primary"],
            font=FONTS["subtitle"],
        ).grid(row=2, column=2, columnspan=2, sticky="e", pady=(6, 0))

        ttk.Button(
            right_card,
            text="Complete Sale & Issue Receipt",
            style="Primary.TButton",
            command=self._checkout,
        ).pack(fill="x")

    def _add_selected_to_cart(self) -> None:
        sel = self.catalog_tree.selection()
        if not sel:
            messagebox.showinfo(
                "Select Medicine", "Select a medicine batch from the left list.", parent=self
            )
            return

        med_id = int(sel[0])
        try:
            add_qty = parse_positive_int(self.add_qty_var.get(), "Quantity")
            existing_qty = self._cart[med_id].quantity if med_id in self._cart else 0
            (
                valid_id,
                name,
                batch,
                price,
                available,
                expiry_date,
            ) = self.sales_service.validate_medicine_for_cart(med_id, existing_qty + add_qty)
        except (ValidationError, BusinessRuleError) as exc:
            messagebox.showerror("Cannot Add to Cart", str(exc), parent=self)
            return

        self._cart[valid_id] = CartItem(
            medicine_id=valid_id,
            medicine_name=name,
            batch_number=batch,
            unit_price=price,
            quantity=existing_qty + add_qty,
            available_stock=available,
            expiry_date=expiry_date,
        )
        self.add_qty_var.set("1")
        self._refresh_cart_ui()

    def _remove_cart_item(self) -> None:
        sel = self.cart_tree.selection()
        if not sel:
            return
        med_id = int(sel[0])
        self._cart.pop(med_id, None)
        self._refresh_cart_ui()

    def _clear_cart(self) -> None:
        self._cart.clear()
        self.amount_paid_var.set("")
        self._refresh_cart_ui()

    def _refresh_cart_ui(self) -> None:
        for row_id in self.cart_tree.get_children():
            self.cart_tree.delete(row_id)

        for item in self._cart.values():
            self.cart_tree.insert(
                "",
                "end",
                iid=str(item.medicine_id),
                values=(
                    item.medicine_name,
                    item.batch_number,
                    item.quantity,
                    format_currency(item.unit_price),
                    format_currency(item.line_total),
                ),
            )
        self._recalculate_summary()

    def _recalculate_summary(self) -> None:
        items = list(self._cart.values())
        try:
            disc = float((self.discount_var.get() or "0").strip())
        except ValueError:
            disc = 0.0
        try:
            tax = float((self.tax_var.get() or "0").strip())
        except ValueError:
            tax = 0.0

        disc = max(0.0, min(100.0, disc))
        tax = max(0.0, min(100.0, tax))

        raw_paid = self.amount_paid_var.get().strip()
        paid_arg: float | None = None
        if raw_paid:
            try:
                paid_arg = max(0.0, float(raw_paid))
            except ValueError:
                paid_arg = None

        subtotal = round(sum(i.line_total for i in items), 2)
        discount_amt = round(subtotal * (disc / 100.0), 2)
        taxable = max(0.0, round(subtotal - discount_amt, 2))
        tax_amt = round(taxable * (tax / 100.0), 2)
        total = round(taxable + tax_amt, 2)
        change = max(0.0, round((paid_arg if paid_arg is not None else total) - total, 2))

        self.subtotal_lbl_var.set(format_currency(subtotal))
        self.discount_lbl_var.set(f"-{format_currency(discount_amt)}")
        self.tax_lbl_var.set(format_currency(tax_amt))
        self.total_lbl_var.set(format_currency(total))
        self.change_lbl_var.set(format_currency(change))

    def _checkout(self) -> None:
        items = list(self._cart.values())
        if not items:
            messagebox.showinfo("Empty Cart", "Add at least one medicine to the cart.", parent=self)
            return

        paid_raw = self.amount_paid_var.get().strip()
        paid_val = paid_raw if paid_raw else None

        try:
            sale = self.sales_service.create_sale(
                cart_items=items,
                customer_name=self.customer_name_var.get(),
                customer_phone=self.customer_phone_var.get(),
                discount_percent=self.discount_var.get() or "0",
                tax_percent=self.tax_var.get() or "0",
                amount_paid=paid_val,
                payment_method=self.payment_method_var.get(),
                notes=self.notes_var.get(),
            )
        except (ValidationError, BusinessRuleError) as exc:
            messagebox.showerror("Checkout Failed", str(exc), parent=self)
            return

        self._cart.clear()
        self.customer_name_var.set("Walk-in Customer")
        self.customer_phone_var.set("")
        self.discount_var.set("0")
        self.amount_paid_var.set("")
        self._refresh_cart_ui()
        self.refresh()

        if self.on_data_changed:
            self.on_data_changed()

        dialog = ReceiptDialog(self, sale)
        self.wait_window(dialog)

    def refresh(self) -> None:
        """Reload catalog list from SQLite."""
        for row_id in self.catalog_tree.get_children():
            self.catalog_tree.delete(row_id)

        medicines = self.inventory_service.list_medicines(
            search_query=self.search_var.get(), status_filter="all"
        )
        self._catalog_by_id = {m.id: m for m in medicines if m.id is not None}

        for med in medicines:
            exp_status = expiry_status_label(med.expiry_date)
            if exp_status == "Expired":
                label = "EXPIRED (Blocked)"
                tags = ("expired",)
            elif med.quantity <= 0:
                label = "Out of Stock"
                tags = ("warning",)
            elif exp_status == "Expiring Soon":
                label = "Expiring Soon"
                tags = ("warning",)
            else:
                label = "Available"
                tags = ()

            self.catalog_tree.insert(
                "",
                "end",
                iid=str(med.id),
                values=(
                    med.name,
                    med.batch_number,
                    format_currency(med.unit_price),
                    med.quantity,
                    med.expiry_date,
                    label,
                ),
                tags=tags,
            )
