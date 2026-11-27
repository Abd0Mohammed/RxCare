# RxCare Pharmacy Management System (Python + Tkinter + SQLite3)

A modular desktop Pharmacy Management System built in Python 3 using standard `tkinter` / `ttk` for the graphical interface and `sqlite3` for ACID-compliant local persistence.

## Features

- **Dashboard Overview**: Live KPIs (today's revenue, invoice count, catalog SKUs, inventory retail value, low-stock count, expiring-soon count, expired count, supplier count), urgent stock/expiry table, and recent transactions.
- **Medicine Inventory Management**: Full CRUD for medicine batches (name, generic name, category, unique batch number, supplier link, cost/selling price, stock quantity, reorder level, expiry date), stock restock/adjustment modal with audit trail, status filtering, and CSV export.
- **Point of Sale (POS)**: Split catalog-and-cart billing screen with live subtotal, discount %, tax %, payment method, tendered cash/change calculation, **strict expiry enforcement** (expired batches are blocked at both cart-add and checkout), **atomic SQLite checkout transactions**, and formatted receipt modal.
- **Supplier Directory**: Full CRUD with search and referential integrity protection (prevents deleting suppliers still linked to active medicine records).
- **Expiry & Stock Alerts**: Dedicated center with configurable warning window (15/30/60/90 days), expired batch quarantine with audited stock write-off, expiring-soon monitoring, and one-click low-stock restocking.
- **Reports & Analytics**: Date-range sales summary, invoice history with receipt re-open, top-selling medicines, category inventory valuation, stock adjustment audit log, and CSV exports.

## Project Structure

```text
main.py                         # Desktop application entry point
requirements.txt                # Runtime notes & optional pytest runner
README.md                       # Setup and usage instructions
DISCUSSION_GUIDE.md             # Architecture & technical walkthrough
pharmacy/
  __init__.py
  config.py                     # Paths, business defaults, theme tokens
  utils.py                      # Validation, expiry checks, formatting, CSV export
  database/
    __init__.py
    db_manager.py               # SQLite3 connection, schema, savepoint transactions, seeding
  models/
    __init__.py
    entities.py                 # Dataclasses (Supplier, Medicine, CartItem, Sale, etc.)
  services/
    __init__.py
    supplier_service.py         # Supplier CRUD & deletion rules
    inventory_service.py        # Medicine CRUD, adjustments, filters, audit log
    sales_service.py            # POS totals, expiry enforcement, atomic checkout
    report_service.py           # Dashboard KPIs, sales analytics, CSV exports
  ui/
    __init__.py
    styles.py                   # ttk styling & dialog centering
    main_window.py              # Main shell, sidebar navigation, status bar, shutdown
    dashboard_view.py           # Dashboard view
    inventory_view.py           # Inventory view + Add/Edit/Restock dialogs
    sales_view.py               # POS view + Receipt dialog
    suppliers_view.py           # Suppliers view + Add/Edit dialog
    alerts_view.py              # Expiry & low-stock alerts view
    reports_view.py             # Reports, audit log, & CSV export view
tests/
  __init__.py
  test_pharmacy_system.py       # Automated unittest suite
```

## Prerequisites

- **Python 3.10+** (tested on Python 3.11)
- **Tkinter** (included with standard Python installers on Windows and macOS; on Debian/Ubuntu Linux install with `sudo apt-get install python3-tk`)

## Running Locally

1. Navigate to the project root directory.
2. Launch the desktop application:
   ```bash
   python main.py
   ```
   *(On Linux/macOS if `python` points to Python 2 or is unavailable, run `python3 main.py`.)*

On first launch, the application creates `data/pharmacy.db` and seeds sample suppliers, medicines (including valid, low-stock, expiring-soon, and expired demo batches), and one sample invoice.

## Running Automated Tests

Run the `unittest` suite without needing a GUI display:

```bash
python3 -m unittest discover -s tests -v
```
