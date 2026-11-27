"""Custom CSS styling, page headers, KPI cards, and status badges for RxCare Web."""

from __future__ import annotations

import html
import streamlit as st

from pharmacy.models.entities import Medicine
from pharmacy.utils import expiry_status_label
from web_app.config import WEB_COLORS


def inject_custom_css() -> None:
    """Inject clean medical-green, white, and light-gray styling."""
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {WEB_COLORS['bg_app']};
                color: {WEB_COLORS['text_primary']};
            }}
            section[data-testid="stSidebar"] {{
                background-color: #0B2E2A;
                border-right: 1px solid #134E4A;
            }}
            section[data-testid="stSidebar"] * {{
                color: #F0FDFA;
            }}
            section[data-testid="stSidebar"] .stRadio > div {{
                gap: 0.35rem;
            }}
            section[data-testid="stSidebar"] label[data-baseweb="radio"] {{
                background-color: rgba(255, 255, 255, 0.04);
                border-radius: 8px;
                padding: 0.45rem 0.7rem;
                transition: background-color 0.15s ease;
            }}
            section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {{
                background-color: rgba(20, 184, 166, 0.18);
            }}
            .rxcare-header {{
                background: {WEB_COLORS['bg_card']};
                border: 1px solid {WEB_COLORS['border']};
                border-left: 5px solid {WEB_COLORS['primary']};
                border-radius: 10px;
                padding: 1rem 1.25rem;
                margin-bottom: 1.1rem;
                box-shadow: 0 1px 2px rgba(15, 41, 38, 0.04);
            }}
            .rxcare-header h1 {{
                margin: 0;
                font-size: 1.45rem;
                font-weight: 700;
                color: {WEB_COLORS['text_primary']};
                letter-spacing: -0.01em;
            }}
            .rxcare-header p {{
                margin: 0.25rem 0 0 0;
                font-size: 0.9rem;
                color: {WEB_COLORS['text_secondary']};
            }}
            .rxcare-kpi-card {{
                background: {WEB_COLORS['bg_card']};
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 10px;
                padding: 0.95rem 1.1rem;
                box-shadow: 0 1px 2px rgba(15, 41, 38, 0.04);
                height: 100%;
                margin-bottom: 0.65rem;
            }}
            .rxcare-kpi-accent {{
                height: 4px;
                border-radius: 4px;
                margin-bottom: 0.65rem;
            }}
            .rxcare-kpi-label {{
                font-size: 0.78rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                color: {WEB_COLORS['text_secondary']};
            }}
            .rxcare-kpi-value {{
                font-size: 1.55rem;
                font-weight: 700;
                color: {WEB_COLORS['text_primary']};
                margin-top: 0.25rem;
                font-variant-numeric: tabular-nums;
            }}
            .rxcare-kpi-sub {{
                font-size: 0.8rem;
                color: {WEB_COLORS['text_secondary']};
                margin-top: 0.2rem;
            }}
            .rxcare-card {{
                background: {WEB_COLORS['bg_card']};
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 10px;
                padding: 1rem 1.15rem;
                margin-bottom: 1rem;
            }}
            .rxcare-badge {{
                display: inline-block;
                padding: 0.18rem 0.55rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 600;
            }}
            div.stButton > button[kind="primary"] {{
                background-color: {WEB_COLORS['primary']};
                border-color: {WEB_COLORS['primary']};
            }}
            div.stButton > button[kind="primary"]:hover {{
                background-color: #0D5E57;
                border-color: #0D5E57;
            }}
            @media (max-width: 768px) {{
                .rxcare-kpi-value {{
                    font-size: 1.25rem;
                }}
                .rxcare-header h1 {{
                    font-size: 1.2rem;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    """Render a consistent top page banner."""
    st.markdown(
        f"""
        <div class="rxcare-header">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(
    label: str,
    value: str,
    accent: str = WEB_COLORS["primary"],
    subtext: str = "",
) -> None:
    """Render a clean KPI metric card."""
    sub_html = (
        f'<div class="rxcare-kpi-sub">{html.escape(subtext)}</div>' if subtext else ""
    )
    st.markdown(
        f"""
        <div class="rxcare-kpi-card">
            <div class="rxcare-kpi-accent" style="background:{accent};"></div>
            <div class="rxcare-kpi-label">{html.escape(label)}</div>
            <div class="rxcare-kpi-value">{html.escape(value)}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def medicine_status_text(med: Medicine, warning_days: int = 30) -> str:
    """Compute a concise status label for a medicine batch."""
    exp_label = expiry_status_label(med.expiry_date, warning_days=warning_days)
    if exp_label == "Expired":
        return "EXPIRED (Blocked)"
    if med.quantity <= 0:
        return "Out of Stock"
    if exp_label == "Expiring Soon":
        return "Expiring Soon"
    if med.quantity <= med.reorder_level:
        return "Low Stock"
    return "In Stock"
