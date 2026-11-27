"""RxCare Pharmacy Management System — Streamlit Web Edition Entry Point.

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
from web_app.config import APP_SUBTITLE, APP_VERSION, BRAND_NAME
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


def main() -> None:
    st.set_page_config(
        page_title=f"{BRAND_NAME} — {APP_SUBTITLE}",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_custom_css()
    try:
        app = get_web_app_container()
    except NotImplementedError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        print(f"RxCare Web startup error: {exc}", file=sys.stderr)
        st.error("Unable to initialize the RxCare Web database. Please verify storage permissions and configuration.")
        return

    WebSessionController.ensure_initialized(st.session_state)

    stats = app.report_service.get_dashboard_stats()
    alert_count = stats.expired_count + stats.expiring_soon_count + stats.low_stock_count

    with st.sidebar:
        st.markdown(f"## 💊 {BRAND_NAME}")
        st.caption(f"{APP_SUBTITLE} • v{APP_VERSION}")
        st.markdown("---")

        pages = [
            "Dashboard",
            "Medicine Management",
            "Point of Sale",
            "Inventory Management",
            "Suppliers",
            f"Expiry Alerts ({alert_count})",
            "Reports",
        ]
        selected_label = st.radio(
            "Navigation",
            pages,
            label_visibility="collapsed",
            key="rxcare_nav_page",
        )

        st.markdown("---")
        st.caption(
            f"Active SKUs: **{stats.total_medicines}**  \n"
            f"Today's Revenue: **{format_currency(stats.today_revenue)}**  \n"
            f"Web DB: `{Path(app.db.db_path).name}`"
        )
        st.caption(
            "Note: Local SQLite storage on ephemeral cloud containers resets on redeploy."
        )

    flash_msg = WebSessionController.consume_flash_success(st.session_state)
    if flash_msg:
        st.success(flash_msg)

    try:
        if selected_label == "Dashboard":
            render_dashboard_page(app)
        elif selected_label == "Medicine Management":
            render_medicines_page(app)
        elif selected_label == "Point of Sale":
            render_pos_page(app)
        elif selected_label == "Inventory Management":
            render_inventory_page(app)
        elif selected_label == "Suppliers":
            render_suppliers_page(app)
        elif selected_label.startswith("Expiry Alerts"):
            render_alerts_page(app)
        elif selected_label == "Reports":
            render_reports_page(app)
    except Exception as exc:
        print(f"RxCare Web page error ({selected_label}): {exc}", file=sys.stderr)
        st.error("An unexpected error occurred while processing your request. Please check your inputs and try again.")


if __name__ == "__main__":
    main()
