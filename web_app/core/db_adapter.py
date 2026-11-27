"""Thread-safe SQLite database adapter and cloud-extensible backend interface.

Why an adapter is needed instead of instantiating Desktop DatabaseManager directly:
1. Desktop DatabaseManager opens sqlite3.connect(..., check_same_thread=True),
   which raises sqlite3.ProgrammingError across Streamlit ScriptRunner worker threads.
2. Desktop DatabaseManager defaults to data/pharmacy.db; the Web Edition must remain
   strictly isolated on data/pharmacy_web.db (or an explicitly configured path/URL).
3. Defining a DatabaseBackend protocol lets a future persistent cloud database
   (e.g., PostgreSQL / managed SQLite) plug in cleanly without rewriting UI pages.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Protocol

from pharmacy.database.db_manager import DatabaseManager
from web_app.config import DEFAULT_WEB_DB_PATH, WEB_DATABASE_URL, WEB_DB_PATH_ENV


class DatabaseBackend(Protocol):
    """Abstract persistence contract for RxCare Web services."""

    db_path: str | Path

    @property
    def connection(self) -> sqlite3.Connection: ...

    def transaction(self) -> Iterator[sqlite3.Connection]: ...

    def initialize_schema(self) -> None: ...

    def is_empty(self) -> bool: ...

    def seed_sample_data(self) -> bool: ...

    def close(self) -> None: ...


class WebSQLiteDatabaseManager(DatabaseManager):
    """Thread-safe SQLite adapter reusing desktop schema, seeding, and savepoint logic.

    Uses check_same_thread=False, WAL mode, and an RLock around transaction boundaries
    so Streamlit reruns and concurrent callbacks execute safely on a single cached DB.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        resolved = resolve_web_db_path(db_path)
        self.db_path: str | Path = resolved
        if str(self.db_path) != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            str(self.db_path),
            isolation_level=None,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.execute("PRAGMA busy_timeout = 5000;")
        if str(self.db_path) != ":memory:":
            self._conn.execute("PRAGMA journal_mode = WAL;")

        self._tx_depth = 0
        self._closed = False
        self.initialize_schema()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Serialize writes safely across Streamlit worker threads using an RLock."""
        with self._lock:
            with super().transaction() as conn:
                yield conn


def resolve_web_db_path(
    explicit_path: str | Path | None = None,
    db_url: str | None = None,
) -> str | Path:
    """Resolve isolated database path for the Web Edition."""
    if explicit_path is not None:
        return explicit_path

    effective_url = (db_url if db_url is not None else WEB_DATABASE_URL).strip()
    if effective_url:
        if effective_url == "sqlite:///:memory:":
            return ":memory:"
        if effective_url.startswith("sqlite:///"):
            return Path(effective_url.removeprefix("sqlite:///"))
        raise NotImplementedError(
            "External cloud database URL configured, but only SQLite is currently implemented. "
            "Provide a sqlite:/// URL, RXCARE_WEB_DB_PATH, or implement a cloud SQL DatabaseBackend."
        )

    if WEB_DB_PATH_ENV:
        return Path(WEB_DB_PATH_ENV)
    return DEFAULT_WEB_DB_PATH


def create_database_backend(
    db_path: str | Path | None = None,
    seed_if_empty: bool = True,
) -> WebSQLiteDatabaseManager:
    """Instantiate the configured web database backend and seed once if empty.

    Future extension point: replace or dispatch inside this factory when an external
    cloud database backend (e.g., PostgreSQL via RXCARE_WEB_DB_URL) is implemented.
    """
    resolved = resolve_web_db_path(explicit_path=db_path)
    db = WebSQLiteDatabaseManager(db_path=resolved)
    if seed_if_empty:
        db.seed_sample_data()
    return db
