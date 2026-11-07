"""Markdown/JSON report writers."""
import json
from pathlib import Path

import pandas as pd


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=lambda o: int(o) if hasattr(o, "__int__") else str(o)),
                    encoding="utf-8", newline="\n")


def validation_md(v: pd.DataFrame) -> str:
    fails = v[v.status == "FAIL"]
    head = (f"# Validation summary\n\n**{len(v)} checks, {len(v) - len(fails)} passed, {len(fails)} failed.** "
            f"Labelled (deliberately injected) anomalies are counted separately and are not failures.\n\n")
    summary = v.groupby("category").agg(checks=("check", "size"), failed=("failures", lambda s: int((s > 0).sum())))
    return head + md_table(summary.reset_index()) + "\n\n## All checks\n\n" + md_table(v) + "\n"


def metrics_md(scores, decisions, kpi, idem) -> str:
    out = ["# Evaluation metrics", "",
           "Engine decisions scored against `ground_truth/ground_truth.csv` (the engine never reads it).", "",
           "## Anomaly detection (per exception type)", "", md_table(scores), "",
           "## Expected decisions on labelled normal cases", "", md_table(decisions), "",
           "## Idempotency", ""]
    out += [f"- **{k}**: {v}" for k, v in idem.items()]
    out += ["", "## Reconciliation KPIs", "", "```json", json.dumps(kpi, indent=2, default=int), "```", ""]
    return "\n".join(out)
