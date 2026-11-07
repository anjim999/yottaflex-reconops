"""Load the generated dataset into PostgreSQL (DATABASE_URL, e.g. Neon) or a local SQLite file."""
import io
import os
import sqlite3
from pathlib import Path

import pandas as pd

from .export import SQL_ORDER, ddl, drop_sql, normalise


def load(tables: dict, sqlite_path: Path) -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        _load_postgres(tables, url)
        return "postgres (DATABASE_URL)"
    _load_sqlite(tables, sqlite_path)
    return f"sqlite ({sqlite_path})"


def _load_postgres(tables, url):
    import psycopg

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute(drop_sql())
        cur.execute(ddl())
        for name in SQL_ORDER:
            df = normalise(name, tables[name])
            buf = io.StringIO()
            df.to_csv(buf, index=False, header=False)
            with cur.copy(f"COPY {name} ({', '.join(df.columns)}) FROM STDIN WITH (FORMAT csv)") as cp:
                cp.write(buf.getvalue())
        conn.commit()


def _load_sqlite(tables, path):
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ddl())
    for name in SQL_ORDER:
        df = normalise(name, tables[name]).astype(object).where(lambda d: d.notna(), None)
        cols = ", ".join(df.columns)
        con.executemany(f"INSERT INTO {name} ({cols}) VALUES ({', '.join('?' * len(df.columns))})",
                        [tuple(int(v) if hasattr(v, "__int__") and not isinstance(v, str) else v for v in r)
                         for r in df.itertuples(index=False, name=None)])
    con.commit()
    bad = con.execute("PRAGMA foreign_key_check").fetchall()
    con.close()
    if bad:
        raise RuntimeError(f"SQLite foreign key violations: {bad[:5]}")


def row_counts(sqlite_path: Path) -> dict:
    con = sqlite3.connect(sqlite_path)
    out = {n: con.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0] for n in SQL_ORDER}
    con.close()
    return out
