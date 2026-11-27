"""Configuration constants for the RxCare Streamlit Web Edition."""

from __future__ import annotations

import os
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_APP_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

# Isolated from desktop database (data/pharmacy.db)
DEFAULT_WEB_DB_PATH = DATA_DIR / "pharmacy_web.db"

# Optional override for future persistent cloud DB integrations
WEB_DATABASE_URL = os.getenv("RXCARE_WEB_DB_URL", "").strip()
WEB_DB_PATH_ENV = os.getenv("RXCARE_WEB_DB_PATH", "").strip()

BRAND_NAME = "RxCare"
APP_VERSION = "2.0.0"

# Dark-first SaaS Pharmacy Palette
WEB_COLORS = {
    "bg_app": "#171717",
    "bg_surface": "#1F1F1F",
    "bg_elevated": "#262626",
    "bg_sidebar": "#121212",
    "border": "#2E2E2E",
    "text_primary": "#FFFFFF",
    "text_secondary": "#A3A3A3",
    "accent": "#B8FF38",
    "accent_hover": "#A3E635",
    "accent_text": "#111111",
    "success": "#4ADE80",
    "success_bg": "rgba(74, 222, 128, 0.14)",
    "warning": "#FBBF24",
    "warning_bg": "rgba(251, 191, 36, 0.14)",
    "danger": "#F87171",
    "danger_bg": "rgba(248, 113, 113, 0.15)",
    "info": "#38BDF8",
    "info_bg": "rgba(56, 189, 248, 0.14)",
    # Legacy alias kept for backward compatibility
    "primary": "#B8FF38",
    "primary_light": "#38BDF8",
    "bg_card": "#1F1F1F",
}
