"""Configuration constants for the RxCare Streamlit Web Edition."""

from __future__ import annotations

import os
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_APP_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

# Isolated from desktop database (data/pharmacy.db)
DEFAULT_WEB_DB_PATH = DATA_DIR / "pharmacy_web.db"

# Optional override for future persistent cloud DB integrations (e.g. PostgreSQL URL)
WEB_DATABASE_URL = os.getenv("RXCARE_WEB_DB_URL", "").strip()
WEB_DB_PATH_ENV = os.getenv("RXCARE_WEB_DB_PATH", "").strip()

BRAND_NAME = "RxCare"
APP_SUBTITLE = "Pharmacy Management Web Edition"
APP_VERSION = "1.0.0"

WEB_COLORS = {
    "primary": "#0F766E",       # Medical teal/green
    "primary_light": "#14B8A6",
    "primary_soft": "#ECFDF5",
    "bg_app": "#F4F7F6",
    "bg_card": "#FFFFFF",
    "border": "#DCE5E2",
    "text_primary": "#0F2926",
    "text_secondary": "#4B635E",
    "success": "#15803D",
    "success_bg": "#DCFCE7",
    "warning": "#B45309",
    "warning_bg": "#FEF3C7",
    "danger": "#B91C1C",
    "danger_bg": "#FEE2E2",
    "info": "#0369A1",
    "info_bg": "#E0F2FE",
}
