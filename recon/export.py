"""Write CSV / JSON / SQL seed files and a checksummed manifest."""
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from .config import GENERATOR_VERSION
from .schema import TABLES

SQL_ORDER = ["merchants", "merchant_fee_schedules", "payment_orders", "payment_attempts", "processor_events", "order_status_history",
             "webhook_deliveries", "settlement_batches", "settlement_lines", "bank_statement_lines",
             "canonical_events", "item_status", "reconciliation_matches", "match_items", "exceptions", "exception_status_history", "resolutions"]
INDEXES = [("merchant_fee_schedules", "merchant_id"), ("payment_orders", "merchant_id"), ("payment_attempts", "payment_id"), ("processor_events", "payment_id"),
           ("canonical_events", "payment_id"), ("webhook_deliveries", "payment_id"), ("order_status_history", "payment_id"),
           ("settlement_lines", "batch_id"), ("settlement_lines", "payment_id"), ("settlement_lines", "event_id"),
           ("match_items", "entity_id"), ("item_status", "item_id"), ("exceptions", "entity_id"),
           ("exception_status_history", "exception_id")]
SQL_TYPE = {"text": "TEXT", "int": "BIGINT", "date": "DATE", "ts": "TIMESTAMPTZ"}


def normalise(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Column order and integer types exactly as in the schema."""
    if name not in TABLES:
        return df
    fields = TABLES[name][2]
    df = df[[f.name for f in fields]].copy()
    for f in fields:
        if f.type == "int":
            df[f.name] = pd.to_numeric(df[f.name]).astype("Int64")
    return df


def write_tables(tables: dict, folder: Path, json_too: bool = True):
    folder.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df = normalise(name, df)
        df.to_csv(folder / f"{name}.csv", index=False, lineterminator="\n")
        if json_too:
            (folder / "json").mkdir(exist_ok=True)
            df.to_json(folder / "json" / f"{name}.json", orient="records", indent=1, force_ascii=False)


def read_tables(folder: Path) -> dict:
    return {p.stem: pd.read_csv(p, dtype=str, keep_default_na=False, na_values=[""]).pipe(_typed, p.stem)
            for p in sorted(folder.glob("*.csv"))}


def _typed(df, name):
    if name in TABLES:
        for f in TABLES[name][2]:
            if f.type == "int" and f.name in df:
                df[f.name] = pd.to_numeric(df[f.name]).astype("Int64")
    return df


def ddl() -> str:
    out = ["-- Generated from recon/schema.py. Portable: PostgreSQL (primary) and SQLite.", ""]
    for name in SQL_ORDER:
        desc, pk, fields = TABLES[name]
        cols = []
        for f in fields:
            c = f"  {f.name} {SQL_TYPE[f.type]}" + (" NOT NULL" if f.required else "")
            if f.unique and f.name != pk:
                c += " UNIQUE"
            if f.allowed:
                vals = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in f.allowed)
                c += f" CHECK ({f.name} IN ({vals}))"
            cols.append(c)
        cols.append(f"  PRIMARY KEY ({pk})")
        for f in fields:
            if f.fk:
                t, c = f.fk.split(".")
                cols.append(f"  FOREIGN KEY ({f.name}) REFERENCES {t}({c})")
        out += [f"-- {desc}", f"CREATE TABLE {name} (", ",\n".join(cols), ");", ""]
    out += [f"CREATE INDEX idx_{t}_{c} ON {t} ({c});" for t, c in INDEXES] + [""]
    return "\n".join(out)


def drop_sql() -> str:
    return "\n".join(f"DROP TABLE IF EXISTS {n} CASCADE;" for n in reversed(SQL_ORDER))


def _sql_value(v) -> str:
    if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)):
        return "NULL"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    return "'" + str(v).replace("'", "''") + "'"


def seed_sql(tables: dict, chunk: int = 500) -> str:
    out = ["-- Seed data. Load after schema.sql.", "BEGIN;"]
    for name in SQL_ORDER:
        if name not in tables:
            continue
        df = normalise(name, tables[name]).astype(object).where(lambda d: d.notna(), None)
        cols = ", ".join(df.columns)
        rows = [f"({', '.join(_sql_value(v) for v in r)})" for r in df.itertuples(index=False, name=None)]
        for i in range(0, len(rows), chunk):
            out.append(f"INSERT INTO {name} ({cols}) VALUES\n" + ",\n".join(rows[i:i + chunk]) + ";")
    out.append("COMMIT;")
    return "\n".join(out)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root: Path, run_config: dict, command: str) -> dict:
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "manifest.json" and p.suffix in {".csv", ".json", ".sql"} and "reports" not in p.parts:
            rows = sum(1 for _ in p.open(encoding="utf-8")) - 1 if p.suffix == ".csv" else None
            files.append({"path": p.relative_to(root).as_posix(), "rows": rows, "bytes": p.stat().st_size,
                          "sha256": sha256(p)})
    manifest = {
        "generator_version": GENERATOR_VERSION, "seed": run_config["seed"], "scale": run_config["scale"],
        "command": command, "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__,
        "provenance": "100% synthetic data generated by this repository. No external, personal or confidential "
                      "data was used; processor, bank and merchant names are fictional.",
        "files": files,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
