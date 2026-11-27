"""Matplotlib chart builders for RxCare Web analytics and reporting."""

from __future__ import annotations

from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from web_app.config import WEB_COLORS


def _empty_chart_figure(title: str, empty_message: str) -> Figure:
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=110)
    fig.patch.set_facecolor(WEB_COLORS["bg_card"])
    ax.set_facecolor(WEB_COLORS["bg_card"])
    ax.text(
        0.5,
        0.5,
        empty_message,
        ha="center",
        va="center",
        fontsize=10,
        color=WEB_COLORS["text_secondary"],
    )
    ax.set_title(title, fontsize=11, fontweight="bold", color=WEB_COLORS["text_primary"])
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return fig


def build_daily_sales_figure(daily_rows: Sequence[dict[str, object]]) -> Figure:
    """Build a dual bar chart of daily revenue and net profit."""
    if not daily_rows:
        return _empty_chart_figure("Daily Revenue vs Net Profit", "No sales data in selected range.")

    fig, ax = plt.subplots(figsize=(8.0, 3.8), dpi=110)
    fig.patch.set_facecolor(WEB_COLORS["bg_card"])
    ax.set_facecolor(WEB_COLORS["bg_card"])

    dates = [str(r.get("date") or "") for r in daily_rows]
    revenues = [float(r.get("revenue") or 0.0) for r in daily_rows]
    profits = [float(r.get("profit") or 0.0) for r in daily_rows]

    x = list(range(len(dates)))
    width = 0.38

    ax.bar(
        [i - width / 2 for i in x],
        revenues,
        width=width,
        color=WEB_COLORS["primary"],
        label="Revenue ($)",
    )
    ax.bar(
        [i + width / 2 for i in x],
        profits,
        width=width,
        color=WEB_COLORS["primary_light"],
        label="Net Profit ($)",
    )

    ax.set_title("Daily Revenue vs Net Profit", fontsize=11, fontweight="bold", color=WEB_COLORS["text_primary"])
    ax.set_xticks(x)
    ax.set_xticklabels(dates, rotation=25, ha="right", fontsize=8.5)
    ax.set_ylabel("Amount ($)", fontsize=9, color=WEB_COLORS["text_secondary"])
    ax.grid(axis="y", linestyle="--", alpha=0.35, color="#94A3B8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()
    return fig


def build_top_medicines_figure(top_rows: Sequence[dict[str, object]]) -> Figure:
    """Build a horizontal bar chart of best-selling medicines by revenue."""
    if not top_rows:
        return _empty_chart_figure("Top-Selling Medicines (Revenue)", "No item sales in selected range.")

    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=110)
    fig.patch.set_facecolor(WEB_COLORS["bg_card"])
    ax.set_facecolor(WEB_COLORS["bg_card"])

    ordered = list(reversed(top_rows[:10]))
    names = [
        f"{str(r.get('medicine_name') or 'Unknown')[:22]} ({str(r.get('batch_number') or '-')})"
        for r in ordered
    ]
    revenues = [float(r.get("total_revenue") or 0.0) for r in ordered]

    ax.barh(names, revenues, color=WEB_COLORS["primary"], height=0.6)
    ax.set_title("Top-Selling Medicines (Revenue)", fontsize=11, fontweight="bold", color=WEB_COLORS["text_primary"])
    ax.set_xlabel("Revenue ($)", fontsize=9, color=WEB_COLORS["text_secondary"])
    ax.tick_params(axis="y", labelsize=8.5)
    ax.grid(axis="x", linestyle="--", alpha=0.35, color="#94A3B8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


def build_category_value_figure(cat_rows: Sequence[dict[str, object]]) -> Figure:
    """Build a horizontal bar chart of inventory retail value by category."""
    if not cat_rows:
        return _empty_chart_figure("Inventory Retail Value by Category", "No inventory categories available.")

    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=110)
    fig.patch.set_facecolor(WEB_COLORS["bg_card"])
    ax.set_facecolor(WEB_COLORS["bg_card"])

    ordered = list(reversed(cat_rows[:10]))
    categories = [str(r.get("category") or "Uncategorized") for r in ordered]
    values = [float(r.get("retail_value") or 0.0) for r in ordered]

    ax.barh(categories, values, color="#0D9488", height=0.58)
    ax.set_title("Inventory Retail Value by Category", fontsize=11, fontweight="bold", color=WEB_COLORS["text_primary"])
    ax.set_xlabel("Retail Value ($)", fontsize=9, color=WEB_COLORS["text_secondary"])
    ax.tick_params(axis="y", labelsize=8.5)
    ax.grid(axis="x", linestyle="--", alpha=0.35, color="#94A3B8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig
