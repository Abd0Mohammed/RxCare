"""Main application window with sidebar navigation, status bar, and clean shutdown."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pharmacy.config import (
    APP_TITLE,
    APP_VERSION,
    COLORS,
    FONTS,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    WINDOW_GEOMETRY,
)
from pharmacy.database.db_manager import DatabaseManager
from pharmacy.services.inventory_service import InventoryService
from pharmacy.services.report_service import ReportService
from pharmacy.services.sales_service import SalesService
from pharmacy.services.supplier_service import SupplierService
from pharmacy.ui.alerts_view import AlertsView
from pharmacy.ui.dashboard_view import DashboardView
from pharmacy.ui.inventory_view import InventoryView
from pharmacy.ui.reports_view import ReportsView
from pharmacy.ui.sales_view import SalesView
from pharmacy.ui.styles import configure_styles
from pharmacy.ui.suppliers_view import SuppliersView
from pharmacy.utils import format_currency


class PharmacyMainWindow:
    """Root desktop shell orchestrating navigation, views, and DB shutdown."""

    def __init__(self, root: tk.Tk, db: DatabaseManager) -> None:
        self.root = root
        self.db = db

        self.supplier_service = SupplierService(db)
        self.inventory_service = InventoryService(db)
        self.sales_service = SalesService(db)
        self.report_service = ReportService(db)

        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        configure_styles(self.root)

        self._nav_buttons: dict[str, tk.Button] = {}
        self._views: dict[str, ttk.Frame] = {}
        self._active_key: str = ""
        self._status_var = tk.StringVar(value="Ready")

        self._build_shell()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.show_view("dashboard")
        self._update_status_bar()

    def _build_shell(self) -> None:
        # Sidebar
        sidebar = tk.Frame(self.root, bg=COLORS["bg_sidebar"], width=225)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=COLORS["bg_sidebar"], padx=18, pady=20)
        brand.pack(fill="x")
        tk.Label(
            brand,
            text="RxCare PMS",
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_on_dark"],
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            brand,
            text="Pharmacy Management",
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_muted_dark"],
            font=FONTS["small"],
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        tk.Frame(sidebar, bg="#1F3E50", height=1).pack(fill="x", padx=14, pady=(0, 12))

        nav_items = [
            ("dashboard", "Dashboard"),
            ("sales", "Sales & POS"),
            ("inventory", "Medicine Inventory"),
            ("suppliers", "Suppliers"),
            ("alerts", "Expiry & Alerts"),
            ("reports", "Reports & Analytics"),
        ]
        for key, label in nav_items:
            btn = tk.Button(
                sidebar,
                text=f"  {label}",
                anchor="w",
                bg=COLORS["bg_sidebar"],
                fg=COLORS["text_on_dark"],
                activebackground=COLORS["bg_sidebar_hover"],
                activeforeground=COLORS["text_on_dark"],
                bd=0,
                relief="flat",
                font=FONTS["body_bold"],
                padx=16,
                pady=11,
                cursor="hand2",
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

        # Sidebar footer
        footer = tk.Frame(sidebar, bg=COLORS["bg_sidebar"], padx=16, pady=14)
        footer.pack(side="bottom", fill="x")
        tk.Label(
            footer,
            text=f"Version {APP_VERSION}\nSQLite3 Local Store",
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_muted_dark"],
            font=FONTS["small"],
            justify="left",
            anchor="w",
        ).pack(fill="x")

        # Main Area + Status Bar
        right_shell = ttk.Frame(self.root, style="App.TFrame")
        right_shell.pack(side="right", fill="both", expand=True)

        self.content_area = ttk.Frame(right_shell, style="App.TFrame", padding=18)
        self.content_area.pack(fill="both", expand=True)

        status_bar = tk.Frame(
            right_shell,
            bg=COLORS["bg_surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=14,
            pady=6,
        )
        status_bar.pack(side="bottom", fill="x")
        tk.Label(
            status_bar,
            textvariable=self._status_var,
            bg=COLORS["bg_surface"],
            fg=COLORS["text_secondary"],
            font=FONTS["small"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Instantiate views
        self._views["dashboard"] = DashboardView(
            self.content_area,
            report_service=self.report_service,
            inventory_service=self.inventory_service,
            sales_service=self.sales_service,
            navigate_callback=self.show_view,
        )
        self._views["sales"] = SalesView(
            self.content_area,
            inventory_service=self.inventory_service,
            sales_service=self.sales_service,
            on_data_changed=self._on_data_changed,
        )
        self._views["inventory"] = InventoryView(
            self.content_area,
            inventory_service=self.inventory_service,
            supplier_service=self.supplier_service,
            report_service=self.report_service,
            on_data_changed=self._on_data_changed,
        )
        self._views["suppliers"] = SuppliersView(
            self.content_area,
            supplier_service=self.supplier_service,
            on_data_changed=self._on_data_changed,
        )
        self._views["alerts"] = AlertsView(
            self.content_area,
            inventory_service=self.inventory_service,
            on_data_changed=self._on_data_changed,
        )
        self._views["reports"] = ReportsView(
            self.content_area,
            report_service=self.report_service,
            sales_service=self.sales_service,
            inventory_service=self.inventory_service,
        )

    def show_view(self, view_key: str) -> None:
        """Switch the active workspace view and refresh its data."""
        if view_key not in self._views:
            return

        if self._active_key and self._active_key in self._views:
            self._views[self._active_key].pack_forget()

        for key, btn in self._nav_buttons.items():
            if key == view_key:
                btn.configure(bg=COLORS["bg_sidebar_active"])
            else:
                btn.configure(bg=COLORS["bg_sidebar"])

        target = self._views[view_key]
        target.pack(fill="both", expand=True)
        self._active_key = view_key

        refresh_fn = getattr(target, "refresh", None)
        if callable(refresh_fn):
            refresh_fn()
        self._update_status_bar()

    def _on_data_changed(self) -> None:
        """Keep badges and status bar synchronized after mutations."""
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        stats = self.report_service.get_dashboard_stats()
        alert_total = stats.expired_count + stats.expiring_soon_count + stats.low_stock_count
        alerts_btn = self._nav_buttons.get("alerts")
        if alerts_btn is not None:
            suffix = f" ({alert_total})" if alert_total > 0 else ""
            alerts_btn.configure(text=f"  Expiry & Alerts{suffix}")

        self._status_var.set(
            f"DB: {self.db.db_path}   |   "
            f"SKUs: {stats.total_medicines}   |   "
            f"Low Stock: {stats.low_stock_count}   |   "
            f"Expired: {stats.expired_count}   |   "
            f"Today's Revenue: {format_currency(stats.today_revenue)}"
        )

    def on_close(self) -> None:
        """Close SQLite connection cleanly and exit the Tkinter loop."""
        try:
            self.db.close()
        finally:
            self.root.destroy()
