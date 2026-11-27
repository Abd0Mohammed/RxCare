"""Dark-first SaaS styling, Cairo/Inter typography, RTL/LTR rules, and KPI components."""

from __future__ import annotations

import html
import streamlit as st

from pharmacy.models.entities import Medicine
from pharmacy.utils import expiry_status_label
from web_app.config import WEB_COLORS
from web_app.core.i18n import t


def inject_custom_css(lang: str = "ar") -> None:
    """Inject dark-first (#171717 / #B8FF38 / #FFFFFF) RTL/LTR responsive CSS."""
    is_rtl = lang == "ar"
    direction = "rtl" if is_rtl else "ltr"
    text_align = "right" if is_rtl else "left"
    border_accent_side = "border-right" if is_rtl else "border-left"
    font_stack = (
        '"Cairo", "Noto Sans Arabic", "Tajawal", "Segoe UI", sans-serif'
        if is_rtl
        else '"Inter", "Cairo", "Segoe UI", sans-serif'
    )

    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

            html, body, .stApp, [class*="css"] {{
                font-family: {font_stack};
            }}

            .stApp {{
                background-color: {WEB_COLORS['bg_app']};
                color: {WEB_COLORS['text_primary']};
                direction: {direction};
            }}

            .main .block-container {{
                direction: {direction};
                text-align: {text_align};
                padding-top: 1.4rem;
                padding-bottom: 2.5rem;
                max-width: 1380px;
            }}

            /* Sidebar styling */
            section[data-testid="stSidebar"] {{
                background-color: {WEB_COLORS['bg_sidebar']};
                border-inline-end: 1px solid {WEB_COLORS['border']};
                direction: {direction};
                text-align: {text_align};
            }}
            section[data-testid="stSidebar"] * {{
                color: {WEB_COLORS['text_primary']};
            }}
            section[data-testid="stSidebar"] .stRadio > div {{
                gap: 0.32rem;
            }}
            section[data-testid="stSidebar"] label[data-baseweb="radio"] {{
                background-color: {WEB_COLORS['bg_surface']};
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 10px;
                padding: 0.5rem 0.75rem;
                transition: border-color 0.15s ease, background-color 0.15s ease;
                direction: {direction};
                text-align: {text_align};
            }}
            section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {{
                border-color: {WEB_COLORS['accent']};
                background-color: {WEB_COLORS['bg_elevated']};
            }}

            /* Header Banner */
            .rxcare-header {{
                background: linear-gradient(135deg, {WEB_COLORS['bg_surface']} 0%, {WEB_COLORS['bg_elevated']} 100%);
                border: 1px solid {WEB_COLORS['border']};
                {border_accent_side}: 4px solid {WEB_COLORS['accent']};
                border-radius: 12px;
                padding: 1.05rem 1.35rem;
                margin-bottom: 1.2rem;
                text-align: {text_align};
            }}
            .rxcare-header h1 {{
                margin: 0;
                font-size: 1.5rem;
                font-weight: 800;
                color: {WEB_COLORS['text_primary']};
                letter-spacing: -0.01em;
            }}
            .rxcare-header p {{
                margin: 0.3rem 0 0 0;
                font-size: 0.92rem;
                color: {WEB_COLORS['text_secondary']};
            }}

            /* KPI Cards */
            .rxcare-kpi-card {{
                background: {WEB_COLORS['bg_surface']};
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 12px;
                padding: 1rem 1.15rem;
                height: 100%;
                margin-bottom: 0.7rem;
                text-align: {text_align};
                transition: border-color 0.15s ease;
            }}
            .rxcare-kpi-card:hover {{
                border-color: #3F3F46;
            }}
            .rxcare-kpi-accent {{
                height: 3px;
                border-radius: 999px;
                margin-bottom: 0.7rem;
            }}
            .rxcare-kpi-label {{
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.02em;
                color: {WEB_COLORS['text_secondary']};
            }}
            .rxcare-kpi-value {{
                font-size: 1.6rem;
                font-weight: 800;
                color: {WEB_COLORS['text_primary']};
                margin-top: 0.25rem;
                font-variant-numeric: tabular-nums;
                direction: ltr;
                unicode-bidi: plaintext;
            }}
            .rxcare-kpi-sub {{
                font-size: 0.8rem;
                color: {WEB_COLORS['text_secondary']};
                margin-top: 0.25rem;
            }}

            /* Forms, Inputs, Metrics & Tabs */
            [data-testid="stForm"],
            [data-testid="stExpander"] {{
                background-color: {WEB_COLORS['bg_surface']};
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 12px;
                direction: {direction};
                text-align: {text_align};
            }}
            .stTextInput input,
            .stNumberInput input,
            .stTextArea textarea,
            .stDateInput input {{
                background-color: {WEB_COLORS['bg_elevated']} !important;
                color: {WEB_COLORS['text_primary']} !important;
                border: 1px solid {WEB_COLORS['border']} !important;
                border-radius: 8px !important;
                text-align: {text_align};
            }}
            [data-baseweb="select"] > div {{
                background-color: {WEB_COLORS['bg_elevated']} !important;
                border: 1px solid {WEB_COLORS['border']} !important;
                border-radius: 8px !important;
                direction: {direction};
            }}

            [data-testid="stMetric"] {{
                background-color: {WEB_COLORS['bg_surface']};
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 10px;
                padding: 0.75rem 0.9rem;
                direction: {direction};
                text-align: {text_align};
            }}
            [data-testid="stMetricLabel"] {{
                color: {WEB_COLORS['text_secondary']} !important;
            }}
            [data-testid="stMetricValue"] {{
                color: {WEB_COLORS['text_primary']} !important;
                font-variant-numeric: tabular-nums;
            }}

            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 0.4rem;
                border-bottom: 1px solid {WEB_COLORS['border']};
                direction: {direction};
            }}
            .stTabs [data-baseweb="tab"] {{
                background-color: {WEB_COLORS['bg_surface']};
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 8px 8px 0 0;
                padding: 0.45rem 0.95rem;
                color: {WEB_COLORS['text_secondary']};
                font-weight: 600;
            }}
            .stTabs [aria-selected="true"] {{
                background-color: {WEB_COLORS['bg_elevated']} !important;
                color: {WEB_COLORS['accent']} !important;
                border-bottom-color: {WEB_COLORS['accent']} !important;
            }}

            /* Tables */
            [data-testid="stDataFrame"] {{
                border: 1px solid {WEB_COLORS['border']};
                border-radius: 10px;
                overflow: hidden;
                direction: {direction};
            }}

            /* Buttons: Accessible Dark-First Accent */
            div.stButton > button[kind="primary"],
            div.stFormSubmitButton > button[kind="primary"] {{
                background-color: {WEB_COLORS['accent']} !important;
                color: {WEB_COLORS['accent_text']} !important;
                border: 1px solid {WEB_COLORS['accent']} !important;
                font-weight: 700 !important;
                border-radius: 8px !important;
            }}
            div.stButton > button[kind="primary"]:hover,
            div.stFormSubmitButton > button[kind="primary"]:hover {{
                background-color: {WEB_COLORS['accent_hover']} !important;
                border-color: {WEB_COLORS['accent_hover']} !important;
            }}
            div.stButton > button[kind="secondary"],
            div.stFormSubmitButton > button[kind="secondary"],
            div.stDownloadButton > button {{
                background-color: {WEB_COLORS['bg_elevated']} !important;
                color: {WEB_COLORS['text_primary']} !important;
                border: 1px solid {WEB_COLORS['border']} !important;
                font-weight: 600 !important;
                border-radius: 8px !important;
            }}
            div.stButton > button[kind="secondary"]:hover,
            div.stDownloadButton > button:hover {{
                border-color: {WEB_COLORS['accent']} !important;
                color: {WEB_COLORS['accent']} !important;
            }}

            /* Alerts & Status Banners */
            [data-testid="stAlert"] {{
                border-radius: 10px;
                direction: {direction};
                text-align: {text_align};
            }}

            hr {{
                border-color: {WEB_COLORS['border']};
            }}

            @media (max-width: 768px) {{
                .main .block-container {{
                    padding-left: 0.85rem;
                    padding-right: 0.85rem;
                }}
                .rxcare-kpi-value {{
                    font-size: 1.28rem;
                }}
                .rxcare-header h1 {{
                    font-size: 1.22rem;
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
    accent: str = WEB_COLORS["accent"],
    subtext: str = "",
) -> None:
    """Render a clean dark-first KPI metric card."""
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


def medicine_status_text(
    med: Medicine, lang: str = "ar", warning_days: int = 30
) -> str:
    """Compute a localized status label for a medicine batch."""
    exp_label = expiry_status_label(med.expiry_date, warning_days=warning_days)
    if exp_label == "Expired":
        return t("status_expired", lang)
    if med.quantity <= 0:
        return t("status_out_of_stock", lang)
    if exp_label == "Expiring Soon":
        return t("status_expiring_soon", lang)
    if med.quantity <= med.reorder_level:
        return t("status_low_stock", lang)
    return t("status_in_stock", lang)
