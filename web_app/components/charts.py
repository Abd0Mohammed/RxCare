"""Dark-first bilingual Matplotlib chart builders for RxCare Web analytics."""

from __future__ import annotations

from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from web_app.config import WEB_COLORS
from web_app.core.arabic_shape import format_arabic_for_matplotlib
from web_app.core.i18n import t, translate_category


def _lbl(text: str, lang: str) -> str:
    return format_arabic_for_matplotlib(text) if lang == "ar" else text


def _style_dark_axes(ax: plt.Axes, fig: Figure) -> None:
    fig.patch.set_facecolor(WEB_COLORS["bg_surface"])
    ax.set_facecolor(WEB_COLORS["bg_surface"])
    ax.tick_params(colors=WEB_COLORS["text_secondary"], labelsize=8.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(WEB_COLORS["border"])
    ax.spines["left"].set_color(WEB_COLORS["border"])


def _empty_chart_figure(title: str, empty_message: str, lang: str) -> Figure:
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=110)
    _style_dark_axes(ax, fig)
    ax.text(
        0.5,
        0.5,
        _lbl(empty_message, lang),
        ha="center",
        va="center",
        fontsize=10,
        color=WEB_COLORS["text_secondary"],
    )
    ax.set_title(
        _lbl(title, lang),
        fontsize=11,
        fontweight="bold",
        color=WEB_COLORS["text_primary"],
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return fig


def build_daily_sales_figure(
    daily_rows: Sequence[dict[str, object]], lang: str = "ar"
) -> Figure:
    """Build a dark-mode dual bar chart of daily revenue and net profit."""
    title = t("chart_daily_title", lang)
    if not daily_rows:
        return _empty_chart_figure(title, t("chart_daily_empty", lang), lang)

    fig, ax = plt.subplots(figsize=(8.0, 3.8), dpi=110)
    _style_dark_axes(ax, fig)

    dates = [str(r.get("date") or "") for r in daily_rows]
    revenues = [float(r.get("revenue") or 0.0) for r in daily_rows]
    profits = [float(r.get("profit") or 0.0) for r in daily_rows]

    x = list(range(len(dates)))
    width = 0.38

    ax.bar(
        [i - width / 2 for i in x],
        revenues,
        width=width,
        color=WEB_COLORS["accent"],
        label=_lbl(t("chart_legend_rev", lang), lang),
    )
    ax.bar(
        [i + width / 2 for i in x],
        profits,
        width=width,
        color=WEB_COLORS["info"],
        label=_lbl(t("chart_legend_profit", lang), lang),
    )

    ax.set_title(
        _lbl(title, lang),
        fontsize=11,
        fontweight="bold",
        color=WEB_COLORS["text_primary"],
    )
    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=25, ha="right", fontsize=8.5, color=WEB_COLORS["text_secondary"])
    ax.set_ylabel(
        _lbl(t("chart_amount_axis", lang), lang),
        fontsize=9,
        color=WEB_COLORS["text_secondary"],
    )
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=WEB_COLORS["border"])
    legend = ax.legend(frameon=False, fontsize=8.5)
    for txt in legend.get_texts():
        txt.set_color(WEB_COLORS["text_primary"])
    fig.tight_layout()
    return fig


def build_top_medicines_figure(
    top_rows: Sequence[dict[str, object]], lang: str = "ar"
) -> Figure:
    """Build a dark-mode horizontal bar chart of best-selling medicines by revenue."""
    title = t("chart_top_title", lang)
    if not top_rows:
        return _empty_chart_figure(title, t("chart_top_empty", lang), lang)

    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=110)
    _style_dark_axes(ax, fig)

    ordered = list(reversed(top_rows[:10]))
    names = [
        _lbl(
            f"{str(r.get('medicine_name') or 'Unknown')[:22]} ({str(r.get('batch_number') or '-')})",
            lang,
        )
        for r in ordered
    ]
    revenues = [float(r.get("total_revenue") or 0.0) for r in ordered]

    ax.barh(names, revenues, color=WEB_COLORS["accent"], height=0.6)
    ax.set_title(
        _lbl(title, lang),
        fontsize=11,
        fontweight="bold",
        color=WEB_COLORS["text_primary"],
    )
    ax.set_xlabel(
        _lbl(t("chart_rev_axis", lang), lang),
        fontsize=9,
        color=WEB_COLORS["text_secondary"],
    )
    ax.tick_params(axis="y", labelsize=8.5, colors=WEB_COLORS["text_primary"])
    ax.grid(axis="x", linestyle="--", alpha=0.35, color=WEB_COLORS["border"])
    fig.tight_layout()
    return fig


def build_category_value_figure(
    cat_rows: Sequence[dict[str, object]], lang: str = "ar"
) -> Figure:
    """Build a dark-mode horizontal bar chart of inventory retail value by category."""
    title = t("chart_cat_title", lang)
    if not cat_rows:
        return _empty_chart_figure(title, t("chart_cat_empty", lang), lang)

    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=110)
    _style_dark_axes(ax, fig)

    ordered = list(reversed(cat_rows[:10]))
    categories = [
        _lbl(translate_category(str(r.get("category") or "General"), lang), lang)
        for r in ordered
    ]
    values = [float(r.get("retail_value") or 0.0) for r in ordered]

    ax.barh(categories, values, color=WEB_COLORS["info"], height=0.58)
    ax.set_title(
        _lbl(title, lang),
        fontsize=11,
        fontweight="bold",
        color=WEB_COLORS["text_primary"],
    )
    ax.set_xlabel(
        _lbl(t("chart_val_axis", lang), lang),
        fontsize=9,
        color=WEB_COLORS["text_secondary"],
    )
    ax.tick_params(axis="y", labelsize=8.5, colors=WEB_COLORS["text_primary"])
    ax.grid(axis="x", linestyle="--", alpha=0.35, color=WEB_COLORS["border"])
    fig.tight_layout()
    return fig
