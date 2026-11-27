"""Supplier management view with CRUD dialogs."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from pharmacy.config import COLORS, FONTS
from pharmacy.models.entities import Supplier
from pharmacy.services.supplier_service import SupplierService
from pharmacy.ui.styles import center_toplevel
from pharmacy.utils import BusinessRuleError, ValidationError


class SupplierDialog(tk.Toplevel):
    """Modal dialog for creating or editing a supplier."""

    def __init__(
        self,
        parent: tk.Misc,
        supplier_service: SupplierService,
        supplier: Supplier | None = None,
    ) -> None:
        super().__init__(parent)
        self.supplier_service = supplier_service
        self.supplier = supplier
        self.saved = False

        self.title("Edit Supplier" if supplier else "Add New Supplier")
        self.configure(bg=COLORS["bg_surface"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.name_var = tk.StringVar(value=supplier.name if supplier else "")
        self.contact_var = tk.StringVar(value=supplier.contact_person if supplier else "")
        self.phone_var = tk.StringVar(value=supplier.phone if supplier else "")
        self.email_var = tk.StringVar(value=supplier.email if supplier else "")
        self.address_var = tk.StringVar(value=supplier.address if supplier else "")

        self._build_form()
        center_toplevel(self, parent, 460, 340)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build_form(self) -> None:
        container = tk.Frame(self, bg=COLORS["bg_surface"], padx=20, pady=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)

        fields = [
            ("Supplier Name *", self.name_var),
            ("Contact Person", self.contact_var),
            ("Phone Number", self.phone_var),
            ("Email Address", self.email_var),
            ("Address", self.address_var),
        ]

        for row_idx, (label, var) in enumerate(fields):
            tk.Label(
                container,
                text=label,
                bg=COLORS["bg_surface"],
                fg=COLORS["text_primary"],
                font=FONTS["body_bold"],
                anchor="w",
            ).grid(row=row_idx, column=0, sticky="w", pady=7, padx=(0, 12))
            entry = ttk.Entry(container, textvariable=var, width=34, font=FONTS["body"])
            entry.grid(row=row_idx, column=1, sticky="ew", pady=7)
            if row_idx == 0:
                entry.focus_set()

        btn_row = tk.Frame(container, bg=COLORS["bg_surface"])
        btn_row.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(18, 0))

        ttk.Button(
            btn_row, text="Cancel", style="Secondary.TButton", command=self.destroy
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_row, text="Save Supplier", style="Primary.TButton", command=self._on_save
        ).pack(side="left")

    def _on_save(self) -> None:
        try:
            if self.supplier and self.supplier.id is not None:
                self.supplier_service.update_supplier(
                    supplier_id=self.supplier.id,
                    name=self.name_var.get(),
                    contact_person=self.contact_var.get(),
                    phone=self.phone_var.get(),
                    email=self.email_var.get(),
                    address=self.address_var.get(),
                )
            else:
                self.supplier_service.create_supplier(
                    name=self.name_var.get(),
                    contact_person=self.contact_var.get(),
                    phone=self.phone_var.get(),
                    email=self.email_var.get(),
                    address=self.address_var.get(),
                )
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
            return

        self.saved = True
        self.destroy()


class SuppliersView(ttk.Frame):
    """Supplier directory with search and Add/Edit/Delete controls."""

    def __init__(
        self,
        parent: tk.Misc,
        supplier_service: SupplierService,
        on_data_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, style="App.TFrame")
        self.supplier_service = supplier_service
        self.on_data_changed = on_data_changed
        self.search_var = tk.StringVar()
        self._suppliers_by_id: dict[int, Supplier] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Supplier Directory", style="Title.TLabel").pack(
            side="left"
        )

        actions = ttk.Frame(header, style="App.TFrame")
        actions.pack(side="right")
        ttk.Button(
            actions, text="+ Add Supplier", style="Primary.TButton", command=self._add_supplier
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions, text="Edit Selected", style="Secondary.TButton", command=self._edit_supplier
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            actions, text="Delete Selected", style="Danger.TButton", command=self._delete_supplier
        ).pack(side="left")

        # Search Bar
        filter_card = tk.Frame(
            self,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        filter_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            filter_card,
            text="Search Suppliers:",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).pack(side="left", padx=(0, 8))

        search_entry = ttk.Entry(filter_card, textvariable=self.search_var, width=38)
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<Return>", lambda _e: self.refresh())

        ttk.Button(
            filter_card, text="Search", style="Secondary.TButton", command=self.refresh
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            filter_card, text="Clear", style="Secondary.TButton", command=self._clear_search
        ).pack(side="left")

        # Table Container
        table_card = tk.Frame(
            self,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        table_card.pack(fill="both", expand=True)

        cols = ("id", "name", "contact", "phone", "email", "address", "meds")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", selectmode="browse")
        for col_id, label, width, anchor in [
            ("id", "ID", 50, "center"),
            ("name", "Supplier Name", 210, "w"),
            ("contact", "Contact Person", 150, "w"),
            ("phone", "Phone", 130, "w"),
            ("email", "Email", 190, "w"),
            ("address", "Address", 230, "w"),
            ("meds", "Linked SKUs", 95, "center"),
        ]:
            self.tree.heading(col_id, text=label)
            self.tree.column(col_id, width=width, anchor=anchor)

        self.tree.tag_configure("alt", background=COLORS["row_alt"])
        self.tree.bind("<Double-1>", lambda _e: self._edit_supplier())

        sb_y = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

    def _clear_search(self) -> None:
        self.search_var.set("")
        self.refresh()

    def _get_selected_supplier(self) -> Supplier | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select Supplier", "Please select a supplier row first.", parent=self)
            return None
        supplier_id = int(selection[0])
        return self._suppliers_by_id.get(supplier_id)

    def _add_supplier(self) -> None:
        dialog = SupplierDialog(self, self.supplier_service)
        self.wait_window(dialog)
        if dialog.saved:
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()

    def _edit_supplier(self) -> None:
        supplier = self._get_selected_supplier()
        if not supplier:
            return
        dialog = SupplierDialog(self, self.supplier_service, supplier=supplier)
        self.wait_window(dialog)
        if dialog.saved:
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()

    def _delete_supplier(self) -> None:
        supplier = self._get_selected_supplier()
        if not supplier or supplier.id is None:
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete supplier '{supplier.name}'?",
            parent=self,
        ):
            return
        try:
            self.supplier_service.delete_supplier(supplier.id)
        except (ValidationError, BusinessRuleError) as exc:
            messagebox.showerror("Cannot Delete Supplier", str(exc), parent=self)
            return

        self.refresh()
        if self.on_data_changed:
            self.on_data_changed()

    def refresh(self) -> None:
        """Reload suppliers table."""
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        suppliers = self.supplier_service.list_suppliers(self.search_var.get())
        self._suppliers_by_id = {s.id: s for s in suppliers if s.id is not None}

        for idx, sup in enumerate(suppliers):
            tags = ("alt",) if idx % 2 == 1 else ()
            self.tree.insert(
                "",
                "end",
                iid=str(sup.id),
                values=(
                    sup.id,
                    sup.name,
                    sup.contact_person,
                    sup.phone,
                    sup.email,
                    sup.address,
                    sup.medicine_count,
                ),
                tags=tags,
            )
