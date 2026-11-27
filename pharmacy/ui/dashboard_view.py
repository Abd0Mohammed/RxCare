"""Dashboard overview view displaying KPI metrics, urgent alerts, and recent sales."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from pharmacy.config import COLORS, FONTS
from pharmacy.services.inventory_service import InventoryService
from pharmacy.services.report_service import ReportService
from pharmacy.services.sales_service import SalesService
from pharmacy.utils import expiry_status_label, format_currency


class DashboardView(ttk.Frame):
    """Executive overview with live KPI cards, alert summary, and recent invoices."""

    def __init__(
        self,
        parent: tk.Misc,
        report_service: ReportService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        navigate_callback: Callable[[str], None],
    ) -> None:
        super().__init__(parent, style="App.TFrame")
        self.report_service = report_service
        self.inventory_service = inventory_service
        self.sales_service = sales_service
        self.navigate = navigate_callback

        self._kpi_vars: dict[str, tk.StringVar] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        # Top header row
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 14))

        ttk.Label(header, text="Pharmacy Dashboard", style="Title.TLabel").pack(
            side="left"
        )

        btn_bar = ttk.Frame(header, style="App.TFrame")
        btn_bar.pack(side="right")
        ttk.Button(
            btn_bar,
            text="+ New Sale (POS)",
            style="Primary.TButton",
            command=lambda: self.navigate("sales"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_bar,
            text="Manage Inventory",
            style="Secondary.TButton",
            command=lambda: self.navigate("inventory"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_bar,
            text="Refresh",
            style="Secondary.TButton",
            command=self.refresh,
        ).pack(side="left")

        # KPI Grid (2 rows x 4 cards)
        kpi_grid = ttk.Frame(self, style="App.TFrame")
        kpi_grid.pack(fill="x", pady=(0, 16))
        for col in range(4):
            kpi_grid.columnconfigure(col, weight=1, uniform="kpi")

        cards = [
            ("today_revenue", "Today's Revenue", COLORS["primary"]),
            ("today_sales", "Today's Invoices", COLORS["info"]),
            ("total_medicines", "Catalog SKUs", COLORS["secondary"]),
            ("stock_value", "Inventory Retail Value", COLORS["success"]),
            ("low_stock", "Low Stock Alerts", COLORS["warning"]),
            ("expiring_soon", "Expiring (30 Days)", COLORS["warning"]),
            ("expired", "Expired (Blocked)", COLORS["danger"]),
            ("suppliers", "Active Suppliers", COLORS["secondary"]),
        ]

        for idx, (key, title, accent) in enumerate(cards):
            row, col = divmod(idx, 4)
            var = tk.StringVar(value="--")
            self._kpi_vars[key] = var
            card = self._create_kpi_card(kpi_grid, title, var, accent)
            card.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=(0 if col == 0 else 6, 0 if col == 3 else 6),
                pady=(0 if row == 0 else 6, 6 if row == 0 else 0),
            )

        # Bottom split panels: Left = Urgent Alerts, Right = Recent Sales
        split = ttk.Frame(self, style="App.TFrame")
        split.pack(fill="both", expand=True)
        split.columnconfigure(0, weight=1, uniform="panel")
        split.columnconfigure(1, weight=1, uniform="panel")
        split.rowconfigure(0, weight=1)

        # Left Panel: Alerts Snapshot
        alerts_card = tk.Frame(
            split,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        alerts_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        alerts_top = tk.Frame(alerts_card, bg=COLORS["bg_surface"])
        alerts_top.pack(fill="x", pady=(0, 8))
        tk.Label(
            alerts_top,
            text="Urgent Stock & Expiry Attention",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["subtitle"],
        ).pack(side="left")
        ttk.Button(
            alerts_top,
            text="View All Alerts",
            style="Secondary.TButton",
            command=lambda: self.navigate("alerts"),
        ).pack(side="right")

        alert_cols = ("name", "batch", "qty", "expiry", "issue")
        self.alerts_tree = ttk.Treeview(
            alerts_card, columns=alert_cols, show="headings", height=10
        )
        for col_id, label, width, anchor in [
            ("name", "Medicine", 180, "w"),
            ("batch", "Batch", 95, "w"),
            ("qty", "Qty", 55, "e"),
            ("expiry", "Expiry", 90, "center"),
            ("issue", "Status", 110, "center"),
        ]:
            self.alerts_tree.heading(col_id, text=label)
            self.alerts_tree.column(col_id, width=width, anchor=anchor)

        self.alerts_tree.tag_configure("expired", background=COLORS["danger_bg"])
        self.alerts_tree.tag_configure("warning", background=COLORS["warning_bg"])

        alert_sb = ttk.Scrollbar(
            alerts_card, orient="vertical", command=self.alerts_tree.yview
        )
        self.alerts_tree.configure(yscrollcommand=alert_sb.set)
        self.alerts_tree.pack(side="left", fill="both", expand=True)
        alert_sb.pack(side="right", fill="y")

        # Right Panel: Recent Sales
        sales_card = tk.Frame(
            split,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        sales_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        sales_top = tk.Frame(sales_card, bg=COLORS["bg_surface"])
        sales_top.pack(fill="x", pady=(0, 8))
        tk.Label(
            sales_top,
            text="Recent Sales Transactions",
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["subtitle"],
        ).pack(side="left")
        ttk.Button(
            sales_top,
            text="Open Reports",
            style="Secondary.TButton",
            command=lambda: self.navigate("reports"),
        ).pack(side="right")

        sales_cols = ("invoice", "customer", "method", "total", "date")
        self.recent_sales_tree = ttk.Treeview(
            sales_card, columns=sales_cols, show="headings", height=10
        )
        for col_id, label, width, anchor in [
            ("invoice", "Invoice #", 130, "w"),
            ("customer", "Customer", 130, "w"),
            ("method", "Method", 85, "center"),
            ("total", "Total", 85, "e"),
            ("date", "Timestamp", 135, "center"),
        ]:
            self.recent_sales_tree.heading(col_id, text=label)
            self.recent_sales_tree.column(col_id, width=width, anchor=anchor)

        sales_sb = ttk.Scrollbar(
            sales_card, orient="vertical", command=self.recent_sales_tree.yview
        )
        self.recent_sales_tree.configure(yscrollcommand=sales_sb.set)
        self.recent_sales_tree.pack(side="left", fill="both", expand=True)
        sales_sb.pack(side="right", fill="y")

    def _create_kpi_card(
        self, parent: tk.Misc, title: str, value_var: tk.StringVar, accent_color: str
    ) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        bar = tk.Frame(card, bg=accent_color, height=4)
        bar.pack(fill="x")

        body = tk.Frame(card, bg=COLORS["bg_surface"], padx=14, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text=title,
            bg=COLORS["bg_surface"],
            fg=COLORS["text_secondary"],
            font=FONTS["small"],
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            body,
            textvariable=value_var,
            bg=COLORS["bg_surface"],
            fg=COLORS["text_primary"],
            font=FONTS["kpi_value"],
            anchor="w",
        ).pack(fill="x", pady=(4, 0))
        return card

    def refresh(self) -> None:
        """Reload all KPIs, alert rows, and recent sales from SQLite."""
        stats = self.report_service.get_dashboard_stats()
        self._kpi_vars["today_revenue"].set(format_currency(stats.today_revenue))
        self._kpi_vars["today_sales"].set(str(stats.today_sales_count))
        self._kpi_vars["total_medicines"].set(
            f"{stats.total_medicines} ({stats.total_stock_units} units)"
        )
        self._kpi_vars["stock_value"].set(format_currency(stats.inventory_retail_value))
        self._kpi_vars["low_stock"].set(str(stats.low_stock_count))
        self._kpi_vars["expiring_soon"].set(str(stats.expiring_soon_count))
        self._kpi_vars["expired"].set(str(stats.expired_count))
        self._kpi_vars["suppliers"].set(str(stats.total_suppliers))

        # Populate alerts table
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)

        seen_ids: set[int] = set()
        for med in self.inventory_service.list_medicines(status_filter="expired"):
            if med.id is not None and med.id not in seen_ids:
                seen_ids.add(med.id)
                self.alerts_tree.insert(
                    "",
                    "end",
                    values=(med.name, med.batch_number, med.quantity, med.expiry_date, "EXPIRED"),
                    tags=("expired",),
                )

        for med in self.inventory_service.list_medicines(status_filter="expiring_soon"):
            if med.id is not None and med.id not in seen_ids:
                seen_ids.add(med.id)
                self.alerts_tree.insert(
                    "",
                    "end",
                    values=(
                        med.name,
                        med.batch_number,
                        med.quantity,
                        med.expiry_date,
                        "Expiring Soon",
                    ),
                    tags=("warning",),
                )

        for med in self.inventory_service.list_medicines(status_filter="low_stock"):
            if med.id is not None and med.id not in seen_ids:
                seen_ids.add(med.id)
                status = expiry_status_label(med.expiry_date)
                label = "Low Stock" if status == "Valid" else f"Low + {status}"
                tag = "expired" if status == "Expired" else "warning"
                self.alerts_tree.insert(
                    "",
                    "end",
                    values=(med.name, med.batch_number, med.quantity, med.expiry_date, label),
                    tags=(tag,),
                )

        # Populate recent sales
        for item in self.recent_sales_tree.get_children():
            self.recent_sales_tree.delete(item)

        for sale in self.sales_service.list_sales(limit=25):
            self.recent_sales_tree.insert(
                "",
                "end",
                values=(
                    sale.invoice_number,
                    sale.customer_name,
                    sale.payment_method,
                    format_currency(sale.total_amount),
                    sale.sale_date,
                ),
            )
