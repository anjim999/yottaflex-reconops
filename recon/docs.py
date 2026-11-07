"""Generate docs/data_dictionary.md from recon/schema.py (so docs can never drift from code)."""
from pathlib import Path

from .schema import TABLES

TYPE = {"text": "string", "int": "integer", "date": "date (YYYY-MM-DD)", "ts": "timestamp (ISO-8601 UTC)"}


def data_dictionary() -> str:
    out = ["# Data dictionary", "",
           "Generated from `recon/schema.py` by `python -m recon docs`. All money is integer **minor units** "
           "(cents, paise; JPY has 0 decimals). All timestamps are UTC.", ""]
    for name, (desc, pk, fields) in TABLES.items():
        out += [f"## `{name}`", "", desc, "", f"Primary key: `{pk}`", "",
                "| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |", "|---|---|---|---|---|---|---|"]
        for f in fields:
            allowed = ", ".join(map(str, f.allowed)) if len(f.allowed) <= 10 else f"{len(f.allowed)} values (see schema)"
            rule = "; ".join(s for s in [f"FK -> `{f.fk}`" if f.fk else "", f"regex `{f.pattern}`" if f.pattern else "", f.rule] if s)
            out.append(f"| `{f.name}` | {TYPE[f.type]} | {'yes' if f.required else 'no'} | {allowed} | {f.unit} | "
                       f"{'yes' if f.unique or f.name == pk else ''} | {rule} |")
        out.append("")
    return "\n".join(out)


def write(root: Path):
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "data_dictionary.md").write_text(data_dictionary(), encoding="utf-8")
