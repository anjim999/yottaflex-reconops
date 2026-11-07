"""Overview KPIs, evaluation metrics, validation, run config and audit trail."""
import csv
import json

from fastapi import APIRouter, Query, Request

from ..db import data_dir, scale
from ..queries import EXCEPTIONS_LIVE

router = APIRouter(prefix="/api", tags=["overview"])


def _json(name: str) -> dict:
    p = data_dir() / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@router.get("/health")
def health(request: Request):
    return {"status": "ok", "backend": request.app.state.db.backend, "scale": scale()}


@router.get("/summary")
def summary(request: Request):
    db = request.app.state.db
    tables = ["merchants", "payment_orders", "payment_attempts", "canonical_events", "webhook_deliveries",
              "settlement_batches", "settlement_lines", "bank_statement_lines", "reconciliation_matches"]
    live = lambda col: (f"SELECT {col} AS k, COUNT(*) AS n FROM ({EXCEPTIONS_LIVE}) x GROUP BY {col} ORDER BY n DESC", ())
    r = db.many({
        "counts": ("SELECT " + ", ".join(f"(SELECT COUNT(*) FROM {t}) AS {t}" for t in tables), (), "one"),
        "captured": ("SELECT COUNT(*) AS n FROM payment_orders WHERE status IN ('CAPTURED','PARTIALLY_REFUNDED','REFUNDED')", (), "one"),
        "status": ("SELECT item_type, recon_status, COUNT(*) AS n FROM item_status GROUP BY item_type, recon_status", ()),
        "by_status": live("status"),
        "by_severity": live("severity"),
        "by_type_status": (f"SELECT exception_type, severity, status, COUNT(*) AS n FROM ({EXCEPTIONS_LIVE}) x "
                           "GROUP BY exception_type, severity, status", ()),
        "open_amt": (f"SELECT currency, SUM(amount_minor) AS amount_minor, COUNT(*) AS n FROM ({EXCEPTIONS_LIVE}) x "
                     "WHERE status <> 'RESOLVED' AND currency IS NOT NULL GROUP BY currency ORDER BY currency", ()),
    })
    counts, status = {k: int(v) for k, v in r["counts"].items()}, r["status"]
    st = {(r["item_type"], r["recon_status"]): r["n"] for r in status}
    of = lambda typ, *ss: sum(st.get((typ, s), 0) for s in ss)
    flow = {
        "orders": counts["payment_orders"],
        "captured_orders": r["captured"]["n"],
        "settleable_events": of("PROCESSOR_EVENT", "MATCHED", "EXCEPTION", "IN_TRANSIT", "OUT_OF_PERIOD", "PARTIAL"),
        "events_matched": of("PROCESSOR_EVENT", "MATCHED"),
        "events_pending": of("PROCESSOR_EVENT", "IN_TRANSIT", "OUT_OF_PERIOD"),
        "events_exception": of("PROCESSOR_EVENT", "EXCEPTION", "PARTIAL"),
        "lines": counts["settlement_lines"], "lines_exception": of("SETTLEMENT_LINE", "EXCEPTION"),
        "batches": counts["settlement_batches"], "batches_matched": of("SETTLEMENT_BATCH", "MATCHED"),
        "batches_exception": of("SETTLEMENT_BATCH", "EXCEPTION", "PARTIAL"),
        "bank_in_scope": of("BANK_LINE", "MATCHED", "EXCEPTION", "PARTIAL"), "bank_matched": of("BANK_LINE", "MATCHED"),
        "bank_exception": of("BANK_LINE", "EXCEPTION", "PARTIAL"), "bank_out_of_scope": of("BANK_LINE", "OUT_OF_SCOPE"),
        "duplicate_webhooks": of("WEBHOOK_DELIVERY", "EXCEPTION"),
    }
    return {"counts": counts, "flow": flow, "item_status": status, "exceptions_by_status": r["by_status"],
            "exceptions_by_severity": r["by_severity"], "exceptions_by_type_status": r["by_type_status"],
            "open_exception_amounts": r["open_amt"], "metrics": _json("reports/metrics.json"),
            "run_config": _json("run_config.json")}


@router.get("/validation")
def validation():
    p = data_dir() / "reports" / "validation_summary.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []
    return {"checks": rows, "reproducibility": _json("reports/reproducibility_report.json"),
            "manifest": _json("manifest.json")}


@router.get("/audit")
def audit(request: Request, limit: int = Query(200, le=2000), role: str | None = None):
    sql = """SELECT h.*, e.exception_type, e.severity, e.entity_id FROM exception_status_history h
             JOIN exceptions e ON e.exception_id = h.exception_id"""
    params = []
    if role:
        sql += " WHERE h.actor_role = ?"
        params.append(role)
    return request.app.state.db.all(sql + " ORDER BY h.changed_at DESC, h.history_id DESC LIMIT ?", params + [limit])


@router.get("/resolutions")
def resolutions(request: Request, limit: int = Query(200, le=2000)):
    return request.app.state.db.all("""SELECT r.*, e.exception_type, e.entity_id FROM resolutions r
                                       JOIN exceptions e ON e.exception_id = r.exception_id
                                       ORDER BY r.resolved_at DESC LIMIT ?""", (limit,))
