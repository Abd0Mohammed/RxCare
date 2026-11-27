"""Medicine inventory management view with CRUD, restocking, and CSV export."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from pharmacy.config import (
    COLORS,
    DEFAULT_LOW_STOCK_THRESHOLD,
    FONTS,
)
from pharmacy.models.entities import Medicine
from pharmacy.services.inventory_service import InventoryService
from pharmacy.services.report_service import ReportService
from pharmacy.services.supplier_service import SupplierService
from pharmacy.ui.styles import center_toplevel
from pharmacy.utils import (
    BusinessRuleError,
    ValidationError,
    expiry_status_label,
    format_currency,
    today_iso,
)

CATEGORIES = (
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
)


class MedicineDialog(tk.Toplevel):
    """Modal dialog for adding or editing a medicine batch."""

    def __init__(
        self,
        parent: tk.Misc,
        inventory_service: InventoryService,
        supplier_service: SupplierService,
        medicine: Medicine | None = None,
    ) -> None:
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.supplier_service = supplier_service
        self.medicine = medicine
        self.saved = False

        self.title("Edit Medicine Batch" if medicine else "Add Medicine Batch")
        self.configure(bg=COLORS["bg_surface"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._suppliers = self.supplier_service.list_suppliers()
        self._supplier_map: dict[str, int | None] = {"(Unassigned)": None}
        for sup in self._suppliers:
            if sup.id is not None:
                self._supplier_map[sup.name] = sup.id

        default_supplier = "(Unassigned)"
        if medicine and medicine.supplier_id is not None:
            for label, sid in self._supplier_map.items():
                if sid == medicine.supplier_id:
                    default_supplier = label
                    break

        self.name_var = tk.StringVar(value=medicine.name if medicine else "")
        self.generic_var = tk.StringVar(value=medicine.generic_name if medicine else "")
        self.category_var = tk.StringVar(
            value=medicine.category if medicine else "General"
        )
        self.batch_var = tk.StringVar(value=medicine.batch_number if medicine else "")
        self.supplier_var = tk.StringVar(value=default_supplier)
        self.cost_var = tk.StringVar(
            value=f"{medicine.cost_price:.2f}" if medicine else "0.00"
        )
        self.price_var = tk.StringVar(
            value=f"{medicine.unit_price:.2f}" if medicine else ""
        )
        self.qty_var = tk.StringVar(
            value=str(medicine.quantity) if medicine else "0"
        )
        self.reorder_var = tk.StringVar(
            value=str(medicine.reorder_level)
            if medicine
            else str(DEFAULT_LOW_STOCK_THRESHOLD)
        )
        self.expiry_var = tk.StringVar(
            value=medicine.expiry_date if medicine else today_iso()
        )
        self.desc_var = tk.StringVar(value=medicine.description if medicine else "")

        self._build_form()
        center_toplevel(self, parent, 540, 520)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build_form(self) -> None:
        container = tk.Frame(self, bg=COLORS["bg_surface"], padx=20, pady=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)

        rows = [
            ("Medicine Name *", "entry", self.name_var, None),
            ("Generic Name", "entry", self.generic_var, None),
            ("Category", "combo", self.category_var, CATEGORIES),
            ("Batch Number *", "entry", self.batch_var, None),
            ("Supplier", "combo", self.supplier_var, list(self._supplier_map.keys())),
            ("Cost Price ($)", "entry", self.cost_var, None),
            ("Unit Selling Price ($) *", "entry", self.price_var, None),
            ("Stock Quantity *", "entry", self.qty_var, None),
            ("Reorder Alert Level", "entry", self.reorder_var, None),
            ("Expiry Date (YYYY-MM-DD) *", "entry", self.expiry_var, None),
            ("Description / Notes", "entry", self.desc_var, None),
        ]

        for idx, (label, kind, var, values) in enumerate(rows):
            tk.Label(
                container,
                text=label,
                bg=COLORS["bg_surface"],
                fg=COLORS["text_primary"],
                font=FONTS["body_bold"],
                anchor="w",
            ).grid(row=idx, column=0, sticky="w", pady=5, padx=(0, 12))

            if kind == "combo":
                widget = ttk.Combobox(
                    container,
                    textvariable=var,
                    values=list(values or ()),
                    state="readonly" if label == "Supplier" else "normal",
                    font=FONTS["body"],
                )
            else:
                widget = ttk.Entry(container, textvariable=var, font=FONTS["body"])
            widget.grid(row=idx, column=1, sticky="ew", pady=5)
            if idx == 0:
                widget.focus_set()

        btn_row = tk.Frame(container, bg=COLORS["bg_surface"])
        btn_row.grid(row=len(rows), column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(
            btn_row, text="Cancel", style="Secondary.TButton", command=self.destroy
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_row, text="Save Medicine", style="Primary.TButton", command=self._on_save
        ).pack(side="left")

    def _on_save(self) -> None:
        supplier_id = self._supplier_map.get(self.supplier_var.get())
        try:
            if self.medicine and self.medicine.id is not None:
                self.inventory_service.update_medicine(
                    medicine_id=self.medicine.id,
                    name=self.name_var.get(),
                    generic_name=self.generic_var.get(),
                    category=self.category_var.get(),
                    batch_number=self.batch_var.get(),
                    supplier_id=supplier_id,
                    cost_price=self.cost_var.get(),
                    unit_price=self.price_var.get(),
                    quantity=self.qty_var.get(),
                    reorder_level=self.reorder_var.get(),
                    expiry_date=self.expiry_var.get(),
                    description=self.desc_var.get(),
                )
            else:
                self.inventory_service.create_medicine(
                    name=self.name_var.get(),
                    generic_name=self.generic_var.get(),
                    category=self.category_var.get(),
                    batch_number=self.batch_var.get(),
                    supplier_id=supplier_id,
                    cost_price=self.cost_var.get(),
                    unit_price=self.price_var.get(),
                    quantity=self.qty_var.get(),
                    reorder_level=self.reorder_var.get(),
                    expiry_date=self.expiry_var.get(),
                    description=self.desc_var.get(),
                )
        except (ValidationError, BusinessRuleError) as exc:
            messagebox.showerror("Invalid Medicine Data", str(exc), parent=self)
            return

        self.saved = True
        self.destroy()


class RestockDialog(tk.Toplevel):
    """Modal dialog for restocking or adjusting a medicine batch."""

    def __init__(
        self,
        parent: tk.Misc,
        inventory_service: InventoryService,
        medicine: Medicine,
    ) -> None:
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.medicine = medicine
        self.saved = False

        self.title(f"Adjust Stock - {medicine.name}")
        self.configure(bg=COLORS["bg_surface"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.delta_var = tk.StringVar(value="10")
        self.reason_var = tk.StringVar(value="Restock")
        self.note_var = tk.StringVar()

        container = tk.Frame(self, bg=COLORS["bg_surface"], padx=20, pady=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)

        tk.Label(
            container,
            text=f"{medicine.name} (Batch: {medicine.batch_number})",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["subtitle"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        tk.Label(
            container,
            text=f"Current Stock: {medicine.quantity} units  |  Expiry: {medicine.expiry_date}",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_secondary"],
            font=FONTS["small"],
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        tk.Label(
            container,
            text="Quantity Change (+ / -):",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).grid(row=2, column=0, sticky="w", pady=6, padx=(0, 10))
        qty_entry = ttk.Entry(container, textvariable=self.delta_var, font=FONTS["body"])
        qty_entry.grid(row=2, column=1, sticky="ew", pady=6)
        qty_entry.focus_set()

        tk.Label(
            container,
            text="Reason:",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).grid(row=3, column=0, sticky="w", pady=6, padx=(0, 10))
        ttk.Combobox(
            container,
            textvariable=self.reason_var,
            values=["Restock", "Supplier Return", "Damage / Spoilage", "Audit Correction"],
            font=FONTS["body"],
        ).grid(row=3, column=1, sticky="ew", pady=6)

        tk.Label(
            container,
            text="Reference Note:",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).grid(row=4, column=0, sticky="w", pady=6, padx=(0, 10))
        ttk.Entry(container, textvariable=self.note_var, font=FONTS["body"]).grid(
            row=4, column=1, sticky="ew", pady=6
        )

        btn_row = tk.Frame(container, bg=COLORS["bg_surface"])
        btn_row.grid(row=5, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(
            btn_row, text="Cancel", style="Secondary.TButton", command=self.destroy
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_row, text="Apply Adjustment", style="Primary.TButton", command=self._apply
        ).pack(side="left")

        center_toplevel(self, parent, 440, 270)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _apply(self) -> None:
        if self.medicine.id is None:
            return
        try:
            self.inventory_service.adjust_stock(
                medicine_id=self.medicine.id,
                delta=self.delta_var.get(),
                reason=self.reason_var.get(),
                reference_note=self.note_var.get(),
            )
        except (ValidationError, BusinessRuleError) as exc:
            messagebox.showerror("Adjustment Error", str(exc), parent=self)
            return

        self.saved = True
        self.destroy()


class InventoryView(ttk.Frame):
    """Full medicine inventory management view."""

    FILTER_MAP = {
        "All Medicines": "all",
        "Available for Sale": "available_for_sale",
        "Low Stock": "low_stock",
        "Expiring Soon (30d)": "expiring_soon",
        "Expired": "expired",
    }

    def __init__(
        self,
        parent: tk.Misc,
        inventory_service: InventoryService,
        supplier_service: SupplierService,
        report_service: ReportService,
        on_data_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, style="App.TFrame")
        self.inventory_service = inventory_service
        self.supplier_service = supplier_service
        self.report_service = report_service
        self.on_data_changed = on_data_changed

        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All Medicines")
        self._medicines_by_id: dict[int, Medicine] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Medicine Inventory", style="Title.TLabel").pack(
            side="left"
        )

        actions = ttk.Frame(header, style="App.TFrame")
        actions.pack(side="right")
        ttk.Button(
            actions, text="+ Add Medicine", style="Primary.TButton", command=self._add_medicine
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            actions, text="Edit", style="Secondary.TButton", command=self._edit_medicine
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            actions, text="Restock / Adjust", style="Secondary.TButton", command=self._restock_medicine
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            actions, text="Export CSV", style="Secondary.TButton", command=self._export_csv
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            actions, text="Delete", style="Danger.TButton", command=self._delete_medicine
        ).pack(side="left")

        # Filter bar
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
            text="Search:",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).pack(side="left", padx=(0, 8))

        search_entry = ttk.Entry(filter_card, textvariable=self.search_var, width=32)
        search_entry.pack(side="left", padx=(0, 12))
        search_entry.bind("<Return>", lambda _e: self.refresh())

        tk.Label(
            filter_card,
            text="Status Filter:",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).pack(side="left", padx=(0, 8))

        filter_combo = ttk.Combobox(
            filter_card,
            textvariable=self.filter_var,
            values=list(self.FILTER_MAP.keys()),
            state="readonly",
            width=22,
        )
        filter_combo.pack(side="left", padx=(0, 10))
        filter_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Button(
            filter_card, text="Apply", style="Secondary.TButton", command=self.refresh
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            filter_card, text="Reset", style="Secondary.TButton", command=self._reset_filters
        ).pack(side="left")

        # Table card
        table_card = tk.Frame(
            self,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        table_card.pack(fill="both", expand=True)

        cols = (
            "id",
            "name",
            "generic",
            "category",
            "batch",
            "supplier",
            "cost",
            "price",
            "qty",
            "reorder",
            "expiry",
            "status",
        )
        self.tree = ttk.Treeview(
            table_card, columns=cols, show="headings", selectmode="browse"
        )
        specs = [
            ("id", "ID", 42, "center"),
            ("name", "Medicine Name", 180, "w"),
            ("generic", "Generic", 130, "w"),
            ("category", "Category", 110, "w"),
            ("batch", "Batch #", 105, "w"),
            ("supplier", "Supplier", 150, "w"),
            ("cost", "Cost", 72, "e"),
            ("price", "Price", 72, "e"),
            ("qty", "Qty", 60, "e"),
            ("reorder", "Min", 50, "e"),
            ("expiry", "Expiry", 92, "center"),
            ("status", "Status", 110, "center"),
        ]
        for col_id, label, width, anchor in specs:
            self.tree.heading(col_id, text=label)
            self.tree.column(col_id, width=width, anchor=anchor)

        self.tree.tag_configure("expired", background=COLORS["danger_bg"])
        self.tree.tag_configure("warning", background=COLORS["warning_bg"])
        self.tree.tag_configure("alt", background=COLORS["row_alt"])
        self.tree.bind("<Double-1>", lambda _e: self._edit_medicine())

        sb_y = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

    def _reset_filters(self) -> None:
        self.search_var.set("")
        self.filter_var.set("All Medicines")
        self.refresh()

    def _selected_medicine(self) -> Medicine | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(
                "Select Medicine", "Please select a medicine batch first.", parent=self
            )
            return None
        return self._medicines_by_id.get(int(sel[0]))

    def _add_medicine(self) -> None:
        dialog = MedicineDialog(self, self.inventory_service, self.supplier_service)
        self.wait_window(dialog)
        if dialog.saved:
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()

    def _edit_medicine(self) -> None:
        med = self._selected_medicine()
        if not med:
            return
        dialog = MedicineDialog(
            self, self.inventory_service, self.supplier_service, medicine=med
        )
        self.wait_window(dialog)
        if dialog.saved:
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()

    def _restock_medicine(self) -> None:
        med = self._selected_medicine()
        if not med:
            return
        dialog = RestockDialog(self, self.inventory_service, med)
        self.wait_window(dialog)
        if dialog.saved:
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()

    def _delete_medicine(self) -> None:
        med = self._selected_medicine()
        if not med or med.id is None:
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{med.name}' (Batch {med.batch_number})?",
            parent=self,
        ):
            return
        try:
            self.inventory_service.delete_medicine(med.id)
        except (ValidationError, BusinessRuleError) as exc:
            messagebox.showerror("Cannot Delete Medicine", str(exc), parent=self)
            return

        self.refresh()
        if self.on_data_changed:
            self.on_data_changed()

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Inventory to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="pharmacy_inventory.csv",
        )
        if not path:
            return
        count = self.report_service.export_inventory_csv(path)
        messagebox.showinfo(
            "Export Complete", f"Exported {count} medicine record(s) to:\n{path}", parent=self
        )

    def refresh(self) -> None:
        """Reload medicines table according to current search and status filters."""
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        status_key = self.FILTER_MAP.get(self.filter_var.get(), "all")
        medicines = self.inventory_service.list_medicines(
            search_query=self.search_var.get(), status_filter=status_key
        )
        self._medicines_by_id = {m.id: m for m in medicines if m.id is not None}

        for idx, med in enumerate(medicines):
            exp_status = expiry_status_label(med.expiry_date)
            if exp_status == "Expired":
                status_text = "EXPIRED"
                tag = ("expired",)
            elif med.quantity == 0:
                status_text = "Out of Stock"
                tag = ("warning",)
            elif exp_status == "Expiring Soon":
                status_text = "Expiring Soon"
                tag = ("warning",)
            elif med.quantity <= med.reorder_level:
                status_text = "Low Stock"
                tag = ("warning",)
            else:
                status_text = "In Stock"
                tag = ("alt",) if idx % 2 == 1 else ()

            self.tree.insert(
                "",
                "end",
                iid=str(med.id),
                values=(
                    med.id,
                    med.name,
                    med.generic_name,
                    med.category,
                    med.batch_number,
                    med.supplier_name,
                    format_currency(med.cost_price),
                    format_currency(med.unit_price),
                    med.quantity,
                    med.reorder_level,
                    med.expiry_date,
                    status_text,
                ),
                tags=tag,
            )
