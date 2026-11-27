"""Application-wide configuration constants and UI theme tokens."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "pharmacy.db"

APP_TITLE = "RxCare Pharmacy Management System"
APP_VERSION = "1.0.0"
WINDOW_GEOMETRY = "1280x780"
MIN_WINDOW_WIDTH = 1080
MIN_WINDOW_HEIGHT = 680

# Business rule defaults
DEFAULT_EXPIRY_WARNING_DAYS = 30
DEFAULT_LOW_STOCK_THRESHOLD = 10
DEFAULT_TAX_PERCENT = 5.0
CURRENCY_SYMBOL = "$"

# UI Theme Palette (Clinical Slate & Teal)
COLORS = {
    "bg_app": "#F4F7F9",
    "bg_surface": "#FFFFFF",
    "bg_sidebar": "#0F2937",
    "bg_sidebar_hover": "#193D50",
    "bg_sidebar_active": "#0D9488",
    "bg_header": "#FFFFFF",
    "border": "#DCE4EA",
    "text_primary": "#13293D",
    "text_secondary": "#52667A",
    "text_on_dark": "#F8FAFC",
    "text_muted_dark": "#9FB3C8",
    "primary": "#0D9488",
    "primary_hover": "#0F766E",
    "secondary": "#334E68",
    "success": "#15803D",
    "success_bg": "#DCFCE7",
    "warning": "#B45309",
    "warning_bg": "#FEF3C7",
    "danger": "#B91C1C",
    "danger_bg": "#FEE2E2",
    "info": "#0369A1",
    "info_bg": "#E0F2FE",
    "row_alt": "#F8FAFC",
}

FONTS = {
    "title": ("Segoe UI", 18, "bold"),
    "subtitle": ("Segoe UI", 12, "bold"),
    "section": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "kpi_value": ("Segoe UI", 22, "bold"),
    "mono": ("Consolas", 10),
}
