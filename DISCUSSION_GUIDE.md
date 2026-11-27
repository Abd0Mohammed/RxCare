# Pharmacy Management System — Technical Discussion Guide

## 1. Architectural Separation
The codebase follows a layered architecture separating persistence, domain models, business services, and Tkinter presentation:

- **Database Layer (`pharmacy/database/db_manager.py`)**: Owns the SQLite connection (`PRAGMA foreign_keys = ON`, `isolation_level=None`), schema creation, explicit `BEGIN IMMEDIATE` / `SAVEPOINT` transaction context management, and graceful shutdown (`close()`).
- **Models (`pharmacy/models/entities.py`)**: Strongly typed dataclasses (`Supplier`, `Medicine`, `CartItem`, `Sale`, `SaleItem`, `StockAdjustment`, `DashboardStats`) decoupled from Tkinter widgets.
- **Service Layer (`pharmacy/services/`)**: Enforces validation, expiry safety policies, atomic POS checkout, referential integrity checks, and reporting queries independently of the GUI.
- **Presentation Layer (`pharmacy/ui/`)**: Modular `ttk.Frame` views orchestrated by `PharmacyMainWindow`, communicating mutations back via lightweight callbacks to keep status bars and alert badges synchronized.

## 2. Database Schema & Integrity
- `suppliers`: Unique supplier names, contact details.
- `medicines`: Unique `batch_number`, `CHECK` constraints (`cost_price >= 0`, `unit_price > 0`, `quantity >= 0`, `reorder_level >= 0`), `supplier_id REFERENCES suppliers(id) ON DELETE RESTRICT`.
- `sales` & `sale_items`: Invoices store `subtotal`, `discount_percent/amount`, `tax_percent/amount`, `total_amount`, `amount_paid`, `change_due`, and snapshot `medicine_name` + `batch_number` on each `sale_items` row so historical invoices remain accurate even if catalog metadata changes.
- `stock_adjustments`: Append-only audit log recording `Initial Stock`, `Manual Edit`, `Restock`, `Expired Write-Off`, and `Sale` deltas.

## 3. Atomic Transactions & Expiry Safety
- `DatabaseManager.transaction()` uses `isolation_level=None` with `BEGIN IMMEDIATE` for outer transactions and `SAVEPOINT` for nested calls.
- `SalesService.create_sale()` re-verifies every cart item inside `BEGIN IMMEDIATE` against live database rows:
  1. Rejects expired batches (`expiry_date <= today`).
  2. Rejects quantities exceeding live `medicines.quantity`.
  3. Uses authoritative database `unit_price` values.
  4. Inserts `sales`, `sale_items`, decrements `medicines.quantity`, and logs `stock_adjustments` atomically. Any error rolls back the entire invoice.

## 4. Known Desktop / Scope Considerations
- **Single-terminal concurrency**: Designed for single-desktop SQLite usage (`busy_timeout=5000`); multi-terminal LAN sharing would require migrating `DatabaseManager` to a client-server database (e.g., PostgreSQL).
- **Headless containers**: Tkinter requires a local windowing environment (`python3-tk` on Linux, native Tk on Windows/macOS) and cannot render windows in headless cloud environments without Tk installed.
