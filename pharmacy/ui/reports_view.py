"""Sales history, analytics, inventory breakdown, and CSV export view."""

from __future__ import annotations

import tkinter as tk
from datetime import timedelta
from tkinter import filedialog, messagebox, ttk

from pharmacy.config import COLORS, FONTS
from pharmacy.services.inventory_service import InventoryService
from pharmacy.services.report_service import ReportService
from pharmacy.services.sales_service import SalesService
from pharmacy.ui.sales_view import ReceiptDialog
from pharmacy.utils import ValidationError, format_currency, parse_iso_date, today_date


class ReportsView(ttk.Frame):
    """Reporting suite for date-range sales, top sellers, categories, and audit logs."""

    def __init__(
        self,
        parent: tk.Misc,
        report_service: ReportService,
        sales_service: SalesService,
        inventory_service: InventoryService,
    ) -> None:
        super().__init__(parent, style="App.TFrame")
        self.report_service = report_service
        self.sales_service = sales_service
        self.inventory_service = inventory_service

        today = today_date()
        self.start_date_var = tk.StringVar(value=(today - timedelta(days=30)).isoformat())
        self.end_date_var = tk.StringVar(value=today.isoformat())

        self._summary_vars = {
            "invoices": tk.StringVar(value="0"),
            "subtotal": tk.StringVar(value=format_currency(0)),
            "discounts": tk.StringVar(value=format_currency(0)),
            "tax": tk.StringVar(value=format_currency(0)),
            "revenue": tk.StringVar(value=format_currency(0)),
        }

        self._build_ui()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Sales & Inventory Reports", style="Title.TLabel").pack(
            side="left"
        )

        export_bar = ttk.Frame(header, style="App.TFrame")
        export_bar.pack(side="right")
        ttk.Button(
            export_bar,
            text="Export Sales CSV",
            style="Primary.TButton",
            command=self._export_sales_csv,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            export_bar,
            text="Export Inventory CSV",
            style="Secondary.TButton",
            command=self._export_inventory_csv,
        ).pack(side="left")

        # Date Filter Row
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
            text="From (YYYY-MM-DD):",
            bg=COLORS["bg_surface"],
            font=FONTS["body_bold"],
        ).pack(side="left", padx=(0, 6))
        ttk.Entry(filter_card, textvariable=self.start_date_var, width=14).pack(
            side="left", padx=(0, 14)
        )

        tk.Label(
            filter_card,
            text="To (YYYY-MM-DD):",
            bg=COLORS["bg_surface"],
            font=FONTS["body_bold"],
        ).pack(side="left", padx=(0, 6))
        ttk.Entry(filter_card, textvariable=self.end_date_var, width=14).pack(
            side="left", padx=(0, 14)
        )

        ttk.Button(
            filter_card,
            text="Generate Report",
            style="Primary.TButton",
            command=self.refresh,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            filter_card,
            text="View Selected Receipt",
            style="Secondary.TButton",
            command=self._open_selected_receipt,
        ).pack(side="right")

        # Summary KPI Strip
        kpi_strip = ttk.Frame(self, style="App.TFrame")
        kpi_strip.pack(fill="x", pady=(0, 12))
        for col in range(5):
            kpi_strip.columnconfigure(col, weight=1, uniform="rep_kpi")

        for col, (key, title) in enumerate(
            [
                ("invoices", "Invoices"),
                ("subtotal", "Gross Subtotal"),
                ("discounts", "Discounts Given"),
                ("tax", "Tax Collected"),
                ("revenue", "Net Revenue"),
            ]
        ):
            card = tk.Frame(
                kpi_strip,
                bg=COLORS["bg_surface"],
                highlightbackground=COLORS["border"],
                highlightthickness=1,
                padx=12,
                pady=10,
            )
            card.grid(
                row=0,
                column=col,
                sticky="nsew",
                padx=(0 if col == 0 else 5, 0 if col == 4 else 5),
            )
            tk.Label(
                card,
                text=title,
                bg=COLORS["bg_surface"],
                fg=COLORS["text_secondary"],
                font=FONTS["small"],
                anchor="w",
            ).pack(fill="x")
            tk.Label(
                card,
                textvariable=self._summary_vars[key],
                bg=COLORS["bg_surface"],
                fg=COLORS["primary"] if key == "revenue" else COLORS["text_primary"],
                font=FONTS["subtitle"],
                anchor="w",
            ).pack(fill="x", pady=(2, 0))

        # Report Tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # Tab 1: Sales Invoices
        sales_tab = tk.Frame(notebook, bg=COLORS["bg_surface"], padx=10, pady=10)
        notebook.add(sales_tab, text="Sales History")
        self.sales_tree = self._build_tree(
            sales_tab,
            cols=("id", "invoice", "date", "customer", "method", "subtotal", "discount", "tax", "total"),
            specs=[
                ("id", "ID", 45, "center"),
                ("invoice", "Invoice #", 145, "w"),
                ("date", "Sale Timestamp", 145, "center"),
                ("customer", "Customer", 160, "w"),
                ("method", "Payment", 110, "center"),
                ("subtotal", "Subtotal", 90, "e"),
                ("discount", "Discount", 85, "e"),
                ("tax", "Tax", 80, "e"),
                ("total", "Grand Total", 100, "e"),
            ],
        )
        self.sales_tree.bind("<Double-1>", lambda _e: self._open_selected_receipt())

        # Tab 2: Top Selling Medicines
        top_tab = tk.Frame(notebook, bg=COLORS["bg_surface"], padx=10, pady=10)
        notebook.add(top_tab, text="Top Selling Medicines")
        self.top_tree = self._build_tree(
            top_tab,
            cols=("rank", "name", "batch", "units", "revenue"),
            specs=[
                ("rank", "#", 50, "center"),
                ("name", "Medicine Name", 280, "w"),
                ("batch", "Batch Number", 150, "w"),
                ("units", "Units Sold", 120, "e"),
                ("revenue", "Gross Revenue", 140, "e"),
            ],
        )

        # Tab 3: Category Valuation
        cat_tab = tk.Frame(notebook, bg=COLORS["bg_surface"], padx=10, pady=10)
        notebook.add(cat_tab, text="Category Breakdown")
        self.category_tree = self._build_tree(
            cat_tab,
            cols=("category", "skus", "units", "value"),
            specs=[
                ("category", "Category", 240, "w"),
                ("skus", "SKU Count", 120, "e"),
                ("units", "Total Stock Units", 150, "e"),
                ("value", "Inventory Retail Value", 170, "e"),
            ],
        )

        # Tab 4: Stock Adjustment Audit Log
        audit_tab = tk.Frame(notebook, bg=COLORS["bg_surface"], padx=10, pady=10)
        notebook.add(audit_tab, text="Stock Audit Log")
        self.audit_tree = self._build_tree(
            audit_tab,
            cols=("id", "timestamp", "medicine", "change", "reason", "note"),
            specs=[
                ("id", "Log ID", 60, "center"),
                ("timestamp", "Timestamp", 150, "center"),
                ("medicine", "Medicine", 220, "w"),
                ("change", "Qty Delta", 90, "e"),
                ("reason", "Reason", 140, "w"),
                ("note", "Reference Note", 240, "w"),
            ],
        )

    @staticmethod
    def _build_tree(
        parent: tk.Misc,
        cols: tuple[str, ...],
        specs: list[tuple[str, str, int, str]],
    ) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        for col_id, label, width, anchor in specs:
            tree.heading(col_id, text=label)
            tree.column(col_id, width=width, anchor=anchor)
        sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    def _validated_date_range(self) -> tuple[str, str] | None:
        try:
            start = parse_iso_date(self.start_date_var.get(), "Start date").isoformat()
            end = parse_iso_date(self.end_date_var.get(), "End date").isoformat()
        except ValidationError as exc:
            messagebox.showerror("Invalid Date Filter", str(exc), parent=self)
            return None
        if start > end:
            messagebox.showerror(
                "Invalid Date Range",
                "Start date cannot be later than End date.",
                parent=self,
            )
            return None
        return start, end

    def _open_selected_receipt(self) -> None:
        sel = self.sales_tree.selection()
        if not sel:
            messagebox.showinfo(
                "Select Invoice", "Select a sales invoice row to view its receipt.", parent=self
            )
            return
        sale = self.sales_service.get_sale(int(sel[0]))
        if not sale:
            messagebox.showerror("Not Found", "Selected invoice could not be loaded.", parent=self)
            return
        dialog = ReceiptDialog(self, sale)
        self.wait_window(dialog)

    def _export_sales_csv(self) -> None:
        dates = self._validated_date_range()
        if not dates:
            return
        start, end = dates
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Sales Report to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"sales_report_{start}_to_{end}.csv",
        )
        if not path:
            return
        count = self.report_service.export_sales_csv(path, start, end)
        messagebox.showinfo(
            "Export Complete", f"Exported {count} invoice(s) to:\n{path}", parent=self
        )

    def _export_inventory_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Inventory Report to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="inventory_report.csv",
        )
        if not path:
            return
        count = self.report_service.export_inventory_csv(path)
        messagebox.showinfo(
            "Export Complete", f"Exported {count} inventory row(s) to:\n{path}", parent=self
        )

    def refresh(self) -> None:
        """Recompute summaries and reload all report tables."""
        dates = self._validated_date_range()
        if not dates:
            return
        start, end = dates

        summary = self.report_service.get_sales_summary_by_range(start, end)
        self._summary_vars["invoices"].set(str(summary["invoice_count"]))
        self._summary_vars["subtotal"].set(format_currency(float(summary["gross_subtotal"])))
        self._summary_vars["discounts"].set(format_currency(float(summary["total_discount"])))
        self._summary_vars["tax"].set(format_currency(float(summary["total_tax"])))
        self._summary_vars["revenue"].set(format_currency(float(summary["net_revenue"])))

        for tree in (self.sales_tree, self.top_tree, self.category_tree, self.audit_tree):
            for row_id in tree.get_children():
                tree.delete(row_id)

        for sale in self.sales_service.list_sales(start_date=start, end_date=end):
            self.sales_tree.insert(
                "",
                "end",
                iid=str(sale.id),
                values=(
                    sale.id,
                    sale.invoice_number,
                    sale.sale_date,
                    sale.customer_name,
                    sale.payment_method,
                    format_currency(sale.subtotal),
                    format_currency(sale.discount_amount),
                    format_currency(sale.tax_amount),
                    format_currency(sale.total_amount),
                ),
            )

        for idx, row in enumerate(
            self.report_service.get_top_selling_medicines(start, end), start=1
        ):
            self.top_tree.insert(
                "",
                "end",
                values=(
                    idx,
                    row["medicine_name"],
                    row["batch_number"],
                    row["units_sold"],
                    format_currency(float(row["total_revenue"])),
                ),
            )

        for row in self.report_service.get_category_inventory_breakdown():
            self.category_tree.insert(
                "",
                "end",
                values=(
                    row["category"],
                    row["sku_count"],
                    row["total_units"],
                    format_currency(float(row["retail_value"])),
                ),
            )

        for adj in self.inventory_service.list_recent_adjustments(limit=100):
            signed_qty = f"+{adj.change_qty}" if adj.change_qty > 0 else str(adj.change_qty)
            self.audit_tree.insert(
                "",
                "end",
                values=(
                    adj.id,
                    adj.created_at,
                    adj.medicine_name,
                    signed_qty,
                    adj.reason,
                    adj.reference_note,
                ),
            )
