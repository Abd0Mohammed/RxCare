"""Expiry monitoring, quarantine write-off, and low-stock alerts view."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from pharmacy.config import COLORS, DEFAULT_EXPIRY_WARNING_DAYS, FONTS
from pharmacy.models.entities import Medicine
from pharmacy.services.inventory_service import InventoryService
from pharmacy.ui.inventory_view import RestockDialog
from pharmacy.utils import BusinessRuleError, ValidationError, days_until_expiry


class AlertsView(ttk.Frame):
    """Dedicated alerts center for expired, expiring-soon, and low-stock medicines."""

    def __init__(
        self,
        parent: tk.Misc,
        inventory_service: InventoryService,
        on_data_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, style="App.TFrame")
        self.inventory_service = inventory_service
        self.on_data_changed = on_data_changed

        self.window_days_var = tk.StringVar(value=str(DEFAULT_EXPIRY_WARNING_DAYS))
        self._expired_map: dict[int, Medicine] = {}
        self._low_stock_map: dict[int, Medicine] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Expiry & Stock Alerts", style="Title.TLabel").pack(
            side="left"
        )

        controls = ttk.Frame(header, style="App.TFrame")
        controls.pack(side="right")
        tk.Label(
            controls,
            text="Expiry Warning Window (days):",
            bg=COLORS["bg_app"],
            fg=COLORS["text_primary"],
            font=FONTS["body_bold"],
        ).pack(side="left", padx=(0, 8))

        combo = ttk.Combobox(
            controls,
            textvariable=self.window_days_var,
            values=["15", "30", "60", "90"],
            state="readonly",
            width=6,
        )
        combo.pack(side="left", padx=(0, 8))
        combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Button(
            controls, text="Refresh", style="Secondary.TButton", command=self.refresh
        ).pack(side="left")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Expired Batches
        expired_tab = tk.Frame(self.notebook, bg=COLORS["bg_surface"], padx=12, pady=12)
        self.notebook.add(expired_tab, text="Expired (Blocked)")

        exp_top = tk.Frame(expired_tab, bg=COLORS["bg_surface"])
        exp_top.pack(fill="x", pady=(0, 8))
        tk.Label(
            exp_top,
            text="These batches are expired and automatically blocked from POS checkout.",
            bg=COLORS["bg_surface"],
            fg=COLORS["danger"],
            font=FONTS["body_bold"],
        ).pack(side="left")
        ttk.Button(
            exp_top,
            text="Write Off Selected Stock",
            style="Danger.TButton",
            command=self._write_off_selected,
        ).pack(side="right")

        self.expired_tree = self._make_alert_tree(
            expired_tab,
            cols=("id", "name", "batch", "supplier", "qty", "expiry", "days"),
            headers=[
                ("id", "ID", 45, "center"),
                ("name", "Medicine", 210, "w"),
                ("batch", "Batch", 110, "w"),
                ("supplier", "Supplier", 170, "w"),
                ("qty", "Remaining Qty", 100, "e"),
                ("expiry", "Expiry Date", 100, "center"),
                ("days", "Days Overdue", 100, "e"),
            ],
            tag_name="expired",
            tag_bg=COLORS["danger_bg"],
        )

        # Tab 2: Expiring Soon
        soon_tab = tk.Frame(self.notebook, bg=COLORS["bg_surface"], padx=12, pady=12)
        self.notebook.add(soon_tab, text="Expiring Soon")

        tk.Label(
            soon_tab,
            text="Batches approaching expiration within the selected warning window.",
            bg=COLORS["bg_surface"],
            fg=COLORS["warning"],
            font=FONTS["body_bold"],
        ).pack(anchor="w", pady=(0, 8))

        self.soon_tree = self._make_alert_tree(
            soon_tab,
            cols=("id", "name", "batch", "supplier", "qty", "expiry", "days"),
            headers=[
                ("id", "ID", 45, "center"),
                ("name", "Medicine", 210, "w"),
                ("batch", "Batch", 110, "w"),
                ("supplier", "Supplier", 170, "w"),
                ("qty", "Qty in Stock", 100, "e"),
                ("expiry", "Expiry Date", 100, "center"),
                ("days", "Days Left", 100, "e"),
            ],
            tag_name="warning",
            tag_bg=COLORS["warning_bg"],
        )

        # Tab 3: Low Stock
        low_tab = tk.Frame(self.notebook, bg=COLORS["bg_surface"], padx=12, pady=12)
        self.notebook.add(low_tab, text="Low Stock")

        low_top = tk.Frame(low_tab, bg=COLORS["bg_surface"])
        low_top.pack(fill="x", pady=(0, 8))
        tk.Label(
            low_top,
            text="Medicines at or below their configured reorder threshold.",
            bg=COLORS["bg_surface"],
            fg=COLORS["warning"],
            font=FONTS["body_bold"],
        ).pack(side="left")
        ttk.Button(
            low_top,
            text="Restock Selected",
            style="Primary.TButton",
            command=self._restock_selected,
        ).pack(side="right")

        self.low_tree = self._make_alert_tree(
            low_tab,
            cols=("id", "name", "batch", "supplier", "qty", "reorder", "expiry"),
            headers=[
                ("id", "ID", 45, "center"),
                ("name", "Medicine", 210, "w"),
                ("batch", "Batch", 110, "w"),
                ("supplier", "Supplier", 170, "w"),
                ("qty", "Current Qty", 100, "e"),
                ("reorder", "Reorder Level", 100, "e"),
                ("expiry", "Expiry Date", 100, "center"),
            ],
            tag_name="warning",
            tag_bg=COLORS["warning_bg"],
        )

    @staticmethod
    def _make_alert_tree(
        parent: tk.Misc,
        cols: tuple[str, ...],
        headers: list[tuple[str, str, int, str]],
        tag_name: str,
        tag_bg: str,
    ) -> ttk.Treeview:
        frame = tk.Frame(parent, bg=COLORS["bg_surface"])
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        for col_id, label, width, anchor in headers:
            tree.heading(col_id, text=label)
            tree.column(col_id, width=width, anchor=anchor)
        tree.tag_configure(tag_name, background=tag_bg)

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    def _write_off_selected(self) -> None:
        sel = self.expired_tree.selection()
        if not sel:
            messagebox.showinfo(
                "Select Batch", "Select an expired batch to write off.", parent=self
            )
            return
        med = self._expired_map.get(int(sel[0]))
        if not med or med.id is None:
            return
        if not messagebox.askyesno(
            "Confirm Expired Write-Off",
            f"Write off {med.quantity} expired unit(s) of '{med.name}' (Batch {med.batch_number})?",
            parent=self,
        ):
            return
        try:
            self.inventory_service.write_off_expired_stock(med.id)
        except (ValidationError, BusinessRuleError) as exc:
            messagebox.showerror("Write-Off Failed", str(exc), parent=self)
            return

        self.refresh()
        if self.on_data_changed:
            self.on_data_changed()

    def _restock_selected(self) -> None:
        sel = self.low_tree.selection()
        if not sel:
            messagebox.showinfo(
                "Select Medicine", "Select a low-stock medicine to restock.", parent=self
            )
            return
        med = self._low_stock_map.get(int(sel[0]))
        if not med:
            return
        dialog = RestockDialog(self, self.inventory_service, med)
        self.wait_window(dialog)
        if dialog.saved:
            self.refresh()
            if self.on_data_changed:
                self.on_data_changed()

    def refresh(self) -> None:
        """Reload all three alert tabs."""
        try:
            warn_days = int(self.window_days_var.get())
        except ValueError:
            warn_days = DEFAULT_EXPIRY_WARNING_DAYS

        for tree in (self.expired_tree, self.soon_tree, self.low_tree):
            for row_id in tree.get_children():
                tree.delete(row_id)

        expired = self.inventory_service.list_medicines(status_filter="expired")
        self._expired_map = {m.id: m for m in expired if m.id is not None}
        for med in expired:
            overdue = abs(days_until_expiry(med.expiry_date))
            self.expired_tree.insert(
                "",
                "end",
                iid=str(med.id),
                values=(
                    med.id,
                    med.name,
                    med.batch_number,
                    med.supplier_name,
                    med.quantity,
                    med.expiry_date,
                    f"{overdue} d",
                ),
                tags=("expired",),
            )

        soon = self.inventory_service.list_medicines(
            status_filter="expiring_soon", warning_days=warn_days
        )
        for med in soon:
            left = days_until_expiry(med.expiry_date)
            self.soon_tree.insert(
                "",
                "end",
                iid=str(med.id),
                values=(
                    med.id,
                    med.name,
                    med.batch_number,
                    med.supplier_name,
                    med.quantity,
                    med.expiry_date,
                    f"{left} d",
                ),
                tags=("warning",),
            )

        low = self.inventory_service.list_medicines(status_filter="low_stock")
        self._low_stock_map = {m.id: m for m in low if m.id is not None}
        for med in low:
            self.low_tree.insert(
                "",
                "end",
                iid=str(med.id),
                values=(
                    med.id,
                    med.name,
                    med.batch_number,
                    med.supplier_name,
                    med.quantity,
                    med.reorder_level,
                    med.expiry_date,
                ),
                tags=("warning",),
            )

        self.notebook.tab(0, text=f"Expired ({len(expired)})")
        self.notebook.tab(1, text=f"Expiring Soon ({len(soon)})")
        self.notebook.tab(2, text=f"Low Stock ({len(low)})")
