"""Centralized ttk styling and reusable Tkinter widget helpers."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pharmacy.config import COLORS, FONTS


def configure_styles(root: tk.Tk) -> ttk.Style:
    """Configure a consistent clinical-slate ttk theme across platforms."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    root.configure(bg=COLORS["bg_app"])

    style.configure("App.TFrame", background=COLORS["bg_app"])
    style.configure("Surface.TFrame", background=COLORS["bg_surface"])
    style.configure(
        "Card.TFrame",
        background=COLORS["bg_surface"],
        borderwidth=1,
        relief="solid",
    )

    style.configure(
        "Title.TLabel",
        background=COLORS["bg_app"],
        foreground=COLORS["text_primary"],
        font=FONTS["title"],
    )
    style.configure(
        "SurfaceTitle.TLabel",
        background=COLORS["bg_surface"],
        foreground=COLORS["text_primary"],
        font=FONTS["subtitle"],
    )
    style.configure(
        "SurfaceBody.TLabel",
        background=COLORS["bg_surface"],
        foreground=COLORS["text_primary"],
        font=FONTS["body"],
    )
    style.configure(
        "SurfaceMuted.TLabel",
        background=COLORS["bg_surface"],
        foreground=COLORS["text_secondary"],
        font=FONTS["small"],
    )
    style.configure(
        "AppMuted.TLabel",
        background=COLORS["bg_app"],
        foreground=COLORS["text_secondary"],
        font=FONTS["small"],
    )

    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground="#FFFFFF",
        font=FONTS["body_bold"],
        padding=(12, 7),
        borderwidth=0,
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_hover"]), ("disabled", "#94A3B8")],
        foreground=[("disabled", "#E2E8F0")],
    )

    style.configure(
        "Secondary.TButton",
        background="#E2E8F0",
        foreground=COLORS["text_primary"],
        font=FONTS["body"],
        padding=(10, 6),
        borderwidth=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", "#CBD5E1")],
    )

    style.configure(
        "Danger.TButton",
        background=COLORS["danger"],
        foreground="#FFFFFF",
        font=FONTS["body_bold"],
        padding=(10, 6),
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#991B1B"), ("disabled", "#FCA5A5")],
    )

    style.configure(
        "Treeview",
        background=COLORS["bg_surface"],
        foreground=COLORS["text_primary"],
        fieldbackground=COLORS["bg_surface"],
        rowheight=28,
        font=FONTS["body"],
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        background="#E8EEF3",
        foreground=COLORS["text_primary"],
        font=FONTS["body_bold"],
        padding=(8, 6),
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", "#CCFBF1")],
        foreground=[("selected", COLORS["text_primary"])],
    )

    style.configure(
        "TNotebook",
        background=COLORS["bg_app"],
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        padding=(14, 7),
        font=FONTS["body_bold"],
    )

    return style


def center_toplevel(window: tk.Toplevel, parent: tk.Misc, width: int, height: int) -> None:
    """Center a modal dialog relative to its parent window."""
    window.update_idletasks()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    x = max(0, px + (pw - width) // 2)
    y = max(0, py + (ph - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
