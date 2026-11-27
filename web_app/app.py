"""RxCare Pharmacy Management System — Bilingual Dark-First Streamlit Entry Point.

Run locally with:
    streamlit run web_app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is importable regardless of launch directory or Streamlit Cloud CWD.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from pharmacy.utils import format_currency
from web_app.components.theme import inject_custom_css
from web_app.config import APP_VERSION, BRAND_NAME, WEB_COLORS
from web_app.core.i18n import NAV_PAGE_KEYS, SUPPORTED_LANGS, t
from web_app.core.web_services import WebAppContainer, WebSessionController
from web_app.pages_ui.alerts_page import render_alerts_page
from web_app.pages_ui.dashboard_page import render_dashboard_page
from web_app.pages_ui.inventory_page import render_inventory_page
from web_app.pages_ui.medicines_page import render_medicines_page
from web_app.pages_ui.pos_page import render_pos_page
from web_app.pages_ui.reports_page import render_reports_page
from web_app.pages_ui.suppliers_page import render_suppliers_page


@st.cache_resource(show_spinner="Initializing RxCare Web database...")
def get_web_app_container() -> WebAppContainer:
    """Create a single shared, thread-safe database + service container per server process."""
    return WebAppContainer(seed_if_empty=True)


def _nav_label(page_key: str, lang: str, alert_count: int) -> str:
    if page_key == "alerts":
        return t("nav_alerts", lang, count=alert_count)
    return t(f"nav_{page_key}", lang)


def main() -> None:
    st.set_page_config(
        page_title=f"{BRAND_NAME} — Pharmacy Management",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    WebSessionController.ensure_initialized(st.session_state)
    lang = WebSessionController.get_lang(st.session_state)
    inject_custom_css(lang=lang)

    try:
        app = get_web_app_container()
    except NotImplementedError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        print(f"RxCare Web startup error: {exc}", file=sys.stderr)
        st.error(t("err_startup", lang))
        return

    stats = app.report_service.get_dashboard_stats()
    alert_count = stats.expired_count + stats.expiring_soon_count + stats.low_stock_count

    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 0.25rem 0 0.5rem 0;">
                <div style="font-size: 1.45rem; font-weight: 800; color: {WEB_COLORS['accent']};">
                    💊 {BRAND_NAME}
                </div>
                <div style="font-size: 0.82rem; color: {WEB_COLORS['text_secondary']};">
                    {t('app_subtitle', lang)} • {t('version_label', lang, version=APP_VERSION)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Persistent language switcher (does not reset cart or active page)
        selected_lang = st.radio(
            t("language_label", lang),
            options=list(SUPPORTED_LANGS),
            format_func=lambda code: t("lang_ar", code) if code == "ar" else t("lang_en", code),
            horizontal=True,
            key=WebSessionController.LANG_KEY,
        )
        if selected_lang != lang:
            lang = selected_lang
            inject_custom_css(lang=lang)

        st.markdown("---")

        # Stable key-based navigation preserves current page and cart across language toggles
        selected_page = st.radio(
            t("nav_label", lang),
            options=list(NAV_PAGE_KEYS),
            format_func=lambda k: _nav_label(k, lang, alert_count),
            label_visibility="collapsed",
            key=WebSessionController.PAGE_KEY,
        )

        st.markdown("---")
        st.caption(
            f"{t('sidebar_skus', lang)}: **{stats.total_medicines}**  \n"
            f"{t('sidebar_today_rev', lang)}: **{format_currency(stats.today_revenue)}**  \n"
            f"{t('sidebar_db', lang)}: `{Path(app.db.db_path).name}`"
        )
        st.caption(t("sidebar_cloud_note", lang))

    flash_msg = WebSessionController.consume_flash_success(st.session_state)
    if flash_msg:
        st.success(flash_msg)

    try:
        if selected_page == "dashboard":
            render_dashboard_page(app, lang=lang)
        elif selected_page == "medicines":
            render_medicines_page(app, lang=lang)
        elif selected_page == "pos":
            render_pos_page(app, lang=lang)
        elif selected_page == "inventory":
            render_inventory_page(app, lang=lang)
        elif selected_page == "suppliers":
            render_suppliers_page(app, lang=lang)
        elif selected_page == "alerts":
            render_alerts_page(app, lang=lang)
        elif selected_page == "reports":
            render_reports_page(app, lang=lang)
    except Exception as exc:
        print(f"RxCare Web page error ({selected_page}): {exc}", file=sys.stderr)
        st.error(t("err_unexpected", lang))


if __name__ == "__main__":
    main()
