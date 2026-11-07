"""Exception queue, detail and analyst/reviewer actions (append-only)."""
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from recon.engine.catalog import EXCEPTIONS
from recon.engine.resolve import EXCEPTION_TRANSITIONS, NOTES
from recon.ids import exception_history_id, resolution_id

from ..queries import EXCEPTIONS_LIVE

router = APIRouter(prefix="/api/exceptions", tags=["exceptions"])
ACTION_TO_STATUS = {"START_REVIEW": "IN_REVIEW", "ESCALATE": "ESCALATED", "RESOLVE": "RESOLVED"}
SORTABLE = {"exception_id", "exception_type", "severity", "status", "amount_minor", "status_changed_at"}


@router.get("")
def list_exceptions(request: Request, type: Optional[str] = None, status: Optional[str] = None,
                    severity: Optional[str] = None, owner: Optional[str] = None, q: Optional[str] = None,
                    sort: str = "exception_id", desc: bool = False, limit: int = Query(50, ge=1, le=500), offset: int = 0):
    where, params = [], []
    for col, val in (("exception_type", type), ("status", status), ("severity", severity), ("owner_role", owner)):
        if val:
            vals = val.split(",")
            where.append(f"{col} IN ({','.join('?' * len(vals))})")
            params += vals
    if q:
        where.append("(exception_id LIKE ? OR entity_id LIKE ? OR related_ids LIKE ? OR description LIKE ?)")
        params += [f"%{q}%"] * 4
    sql = f"SELECT * FROM ({EXCEPTIONS_LIVE}) x" + (f" WHERE {' AND '.join(where)}" if where else "")
    db = request.app.state.db
    order = sort if sort in SORTABLE else "exception_id"
    r = db.many({"total": (f"SELECT COUNT(*) AS n FROM ({sql}) c", params, "one"),
                 "items": (f"{sql} ORDER BY {order} {'DESC' if desc else 'ASC'}, exception_id LIMIT ? OFFSET ?",
                           params + [limit, offset])})
    return {"total": r["total"]["n"], "items": r["items"]}


@router.get("/facets")
def facets(request: Request):
    return request.app.state.db.many({
        col: (f"SELECT {col} AS value, COUNT(*) AS n FROM ({EXCEPTIONS_LIVE}) x GROUP BY {col} ORDER BY n DESC", ())
        for col in ("exception_type", "status", "severity", "owner_role")})


@router.get("/{exception_id}")
def get_exception(exception_id: str, request: Request):
    db = request.app.state.db
    r = db.many({
        "x": (f"SELECT * FROM ({EXCEPTIONS_LIVE}) x WHERE exception_id = ?", (exception_id,), "one"),
        "history": ("SELECT * FROM exception_status_history WHERE exception_id = ? ORDER BY history_id", (exception_id,)),
        "resolution": ("SELECT * FROM resolutions WHERE exception_id = ?", (exception_id,), "one"),
    })
    x = r["x"]
    if not x:
        raise HTTPException(404, "exception not found")
    x["history"], x["resolution"] = r["history"], r["resolution"]
    x["allowed_actions"] = [a for a, s in ACTION_TO_STATUS.items() if s in EXCEPTION_TRANSITIONS[x["status"]]]
    x["default_resolution"] = EXCEPTIONS[x["exception_type"]][2]
    return x


class Action(BaseModel):
    action: Literal["START_REVIEW", "ESCALATE", "RESOLVE"]
    actor_role: Literal["OPS_ANALYST", "RISK_REVIEWER"]
    resolution_type: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    adjustment_amount_minor: Optional[int] = None


@router.post("/{exception_id}/actions")
def act(exception_id: str, body: Action, request: Request):
    """Appends a status-history row (and a resolution on RESOLVE). Nothing is updated in place."""
    db = request.app.state.db
    x = db.one(f"SELECT * FROM ({EXCEPTIONS_LIVE}) x WHERE exception_id = ?", (exception_id,))
    if not x:
        raise HTTPException(404, "exception not found")
    target = ACTION_TO_STATUS[body.action]
    if target not in EXCEPTION_TRANSITIONS[x["status"]]:
        raise HTTPException(409, f"cannot {body.action} an exception that is {x['status']}")
    if body.action == "RESOLVE" and x["owner_role"] == "RISK_REVIEWER" and body.actor_role != "RISK_REVIEWER":
        raise HTTPException(403, "segregation of duties: risk-owned exceptions must be resolved by RISK_REVIEWER")
    if body.action in ("START_REVIEW", "ESCALATE") and body.actor_role != "OPS_ANALYST":
        raise HTTPException(403, f"{body.action} is an OPS_ANALYST action")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with db.tx() as run:
        hid = exception_history_id(_next_no(run, "SELECT MAX(history_id) FROM exception_status_history"))
        run("INSERT INTO exception_status_history (history_id, exception_id, from_status, to_status, changed_at, actor_role) "
            "VALUES (?, ?, ?, ?, ?, ?)", (hid, exception_id, x["status"], target, now, body.actor_role))
        if body.action == "RESOLVE":
            rid = resolution_id(_next_no(run, "SELECT MAX(resolution_id) FROM resolutions"))
            rtype = body.resolution_type or EXCEPTIONS[x["exception_type"]][2]
            amount = body.adjustment_amount_minor if body.adjustment_amount_minor is not None else (x["amount_minor"] or 0)
            run("INSERT INTO resolutions (resolution_id, exception_id, resolution_type, resolved_by_role, resolved_at, "
                "adjustment_amount_minor, currency, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (rid, exception_id, rtype, body.actor_role, now, int(amount), x["currency"],
                 body.notes or NOTES.get(rtype, "Resolved via console.")))
    return get_exception(exception_id, request)


def _next_no(run, sql: str) -> int:
    """Next zero-padded counter after the current max ID (IDs are immutable and never reused)."""
    row = run(sql).fetchone()
    last = next(iter(row.values())) if isinstance(row, dict) else row[0]
    return int(last[-6:]) + 1 if last else 1
