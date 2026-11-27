"""Entry point for the RxCare Pharmacy Management System desktop application."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from pharmacy.config import DEFAULT_DB_PATH
from pharmacy.database.db_manager import DatabaseManager
from pharmacy.ui.main_window import PharmacyMainWindow


def launch_application(db_path: str | Path | None = None, seed_if_empty: bool = True) -> int:
    """Initialize SQLite storage, start the Tkinter main loop, and exit cleanly."""
    db: DatabaseManager | None = None
    try:
        db = DatabaseManager(db_path=db_path or DEFAULT_DB_PATH)
        if seed_if_empty:
            db.seed_sample_data()

        root = tk.Tk()
        PharmacyMainWindow(root=root, db=db)
        root.mainloop()
        return 0
    except Exception as exc:
        if db is not None:
            db.close()
        try:
            err_root = tk.Tk()
            err_root.withdraw()
            messagebox.showerror(
                "Application Startup Error",
                f"Failed to start Pharmacy Management System:\n{exc}",
            )
            err_root.destroy()
        except Exception:
            print(f"Fatal startup error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(launch_application())
