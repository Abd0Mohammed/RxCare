# RxCare Pharmacy Management System — Web Edition (Streamlit)

The **RxCare Web Edition** is an independently executable Streamlit web interface built alongside the original Tkinter Desktop application. It reuses the core domain entities, validation utilities, and service layer (`SupplierService`, `InventoryService`, `SalesService`, `ReportService`) while preserving all desktop code untouched.

## Architecture & Business Logic Reuse

- **Shared Domain & Services (`pharmacy/`)**: Validation, expiry policies, inventory adjustments, atomic checkout transactions, and supplier safeguards are reused directly.
- **Thread-Safe Web Database Adapter (`web_app/core/db_adapter.py`)**:
  - The desktop `DatabaseManager` uses `sqlite3.connect(..., check_same_thread=True)` and defaults to `data/pharmacy.db`.
  - Because Streamlit executes script reruns across worker threads, `WebSQLiteDatabaseManager` configures `check_same_thread=False`, WAL journaling, and a `threading.RLock` around transaction boundaries while isolating web data in `data/pharmacy_web.db`.
  - `create_database_backend()` defines a `DatabaseBackend` protocol and checks `RXCARE_WEB_DB_URL` as an extension point for a future managed cloud database (e.g., PostgreSQL).
- **Web Analytics & Session Controller (`web_app/core/web_services.py`)**:
  - `WebAnalyticsService` adds net profit calculations (`unit_price - cost_price` minus invoice discounts), daily sales/profit trends, and therapeutic category filtering without altering desktop services.
  - `WebSessionController` manages the POS shopping cart and uses a one-time transaction token (`rxcare_pos_tx_token`) so Streamlit reruns cannot accidentally double-charge or duplicate a sale.

## Pages Included

1. **Dashboard**: Total medicines, low-stock count, expired count, expiring-soon count, today's sales, total net profit, urgent alerts, and recent invoices.
2. **Medicine Management**: Add, edit, delete (with confirmation), search, category filter, and batch detail inspection.
3. **Point of Sale (POS)**: Searchable catalog, session cart, quantity updates, subtotal/discount/tax/profit preview, strict expiry blocking, atomic checkout, and invoice summary.
4. **Inventory Management**: Live stock monitoring, low-stock filters, audited stock adjustments, CSV download, and stock audit log.
5. **Suppliers**: Full supplier CRUD with search and deletion protection when linked to medicines.
6. **Expiry Alerts**: Configurable warning window (15/30/60/90 days), expired batch quarantine with confirmed write-off, near-expiry tracking, and quick low-stock restocking.
7. **Reports**: Date-range filters, daily revenue vs. profit Matplotlib chart, best-selling medicines chart, category inventory valuation chart, invoice history, and CSV export.

## Local Startup Instructions

1. Install Web Edition dependencies (Python 3.10+):
   ```bash
   pip install -r web_app/requirements.txt
   ```
2. Start the Streamlit app from the repository root:
   ```bash
   streamlit run web_app/app.py
   ```
3. Open the local URL printed by Streamlit (typically `http://localhost:8501`).

> The Desktop Edition (`python3 main.py`) remains completely separate and uses `data/pharmacy.db`, while the Web Edition uses `data/pharmacy_web.db`.

## Streamlit Community Cloud Deployment Instructions

1. Push this repository (containing `pharmacy/` and `web_app/`) to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and click **New app**.
3. Configure deployment settings:
   - **Repository**: `<your-github-repo>`
   - **Branch**: `main`
   - **Main file path**: `web_app/app.py`
   - **Python version**: `3.11` (recommended)
4. Streamlit Community Cloud automatically detects `web_app/requirements.txt` alongside `web_app/app.py` and reads `.streamlit/config.toml` from the repository root. No Tkinter package is required.
5. Click **Deploy**.

## Important Persistence Limitation (Cloud Hosting)

The initial Web Edition stores data in a local SQLite file (`data/pharmacy_web.db`) for zero-configuration demonstration and local usage. **On ephemeral cloud platforms such as Streamlit Community Cloud, local filesystem storage is temporary and may be reset when the container restarts, sleeps, or redeploys.**

Note on `RXCARE_WEB_DB_URL`: Only local `sqlite:///` URLs (and `RXCARE_WEB_DB_PATH`) are currently implemented. External database URLs (such as `postgresql://`) are not yet implemented and will raise `NotImplementedError` until a cloud `DatabaseBackend` adapter is added in `web_app/core/db_adapter.py`.

## Automated Tests

Run both the Desktop and Web Edition backend test suites:

```bash
python3 -m unittest discover -s tests -v
```
