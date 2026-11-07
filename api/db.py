"""Tiny DB layer: PostgreSQL (DATABASE_URL, e.g. Neon) or the local SQLite file built by `python -m recon load-db`."""
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def scale() -> str:
    return os.getenv("RECON_SCALE", "starter")


def data_dir() -> Path:
    return Path(os.getenv("RECON_DATA_DIR", ROOT / "data" / scale()))


class DB:
    def __init__(self):
        self.url = os.getenv("DATABASE_URL")
        self.sqlite_path = data_dir() / "recon.sqlite"
        self._pool = None
        self._lock = threading.Lock()

    def _pg_pool(self):
        """One pooled set of TLS connections to Postgres/Neon, opened lazily and reused across requests."""
        with self._lock:
            if self._pool is None:
                from psycopg.rows import dict_row
                from psycopg_pool import ConnectionPool

                self._pool = ConnectionPool(self.url, min_size=1, max_size=8, open=True,
                                            kwargs={"row_factory": dict_row, "autocommit": True})
        return self._pool

    @property
    def backend(self) -> str:
        return "postgres" if self.url else "sqlite"

    @contextmanager
    def connect(self):
        if self.url:
            with self._pg_pool().connection() as conn:  # autocommit reads: one network round trip per query
                yield conn
        else:
            if not self.sqlite_path.exists():
                raise RuntimeError(f"{self.sqlite_path} not found - run: python -m recon all --scale {scale()}")
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.url else sql

    def all(self, sql: str, params=()) -> list[dict]:
        with self.connect() as c:
            return [dict(r) for r in c.execute(self._sql(sql), params).fetchall()]

    def one(self, sql: str, params=()):
        rows = self.all(sql, params)
        return rows[0] if rows else None

    def many(self, queries: dict) -> dict:
        """Run independent read queries {name: (sql, params[, "one"])}; in parallel on Postgres to hide network latency."""
        def run(q):
            sql, params, *mode = q
            return self.one(sql, params) if mode == ["one"] else self.all(sql, params)

        if not self.url:
            return {k: run(q) for k, q in queries.items()}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {k: ex.submit(run, q) for k, q in queries.items()}
            return {k: f.result() for k, f in futures.items()}

    @contextmanager
    def tx(self):
        """Yields exec(sql, params) bound to one explicit transaction (all-or-nothing writes)."""
        with self.connect() as c:
            if self.url:
                with c.transaction():
                    yield lambda sql, params=(): c.execute(self._sql(sql), params)
            else:
                yield lambda sql, params=(): c.execute(self._sql(sql), params)
