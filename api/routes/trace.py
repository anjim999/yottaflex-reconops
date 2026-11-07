"""Traceability: from any record ID to its matches, counterpart records and exceptions."""
from fastapi import APIRouter, HTTPException, Request

from ..queries import ENTITY_TABLE, EXCEPTIONS_LIVE, entity_type_of

router = APIRouter(prefix="/api/trace", tags=["trace"])


@router.get("/{entity_id}")
def trace(entity_id: str, request: Request):
    db = request.app.state.db
    etype = entity_type_of(entity_id)
    if not etype:
        raise HTTPException(400, "unknown id prefix")
    table, key = ENTITY_TABLE[etype]
    record = db.one(f"SELECT * FROM {table} WHERE {key} = ?", (entity_id,))
    if record is None and etype == "PROCESSOR_EVENT":
        record = db.one("SELECT * FROM processor_events WHERE event_id = ?", (entity_id,))
    if record is None:
        raise HTTPException(404, f"{entity_id} not found")
    r = db.many({
        "matches": ("SELECT m.*, i.entity_type, i.entity_id, i.side FROM match_items i "
                    "JOIN reconciliation_matches m ON m.match_id = i.match_id "
                    "WHERE i.match_id IN (SELECT match_id FROM match_items WHERE entity_id = ?) "
                    "ORDER BY m.match_id, i.side, i.entity_id", (entity_id,)),
        "exceptions": (f"SELECT * FROM ({EXCEPTIONS_LIVE}) x WHERE entity_id = ? OR related_ids LIKE ? ORDER BY exception_id",
                       (entity_id, f"%{entity_id}%")),
        "status": ("SELECT recon_status, reason FROM item_status WHERE item_id = ?", (entity_id,), "one"),
    })
    matches, exceptions, status = r["matches"], r["exceptions"], r["status"]
    out = {"entity_type": etype, "entity_id": entity_id, "record": record, "recon_status": status,
           "matches": matches, "exceptions": exceptions}
    if etype == "SETTLEMENT_BATCH":
        out["line_summary"] = db.one("""SELECT COUNT(*) AS lines, SUM(CASE WHEN line_type='CAPTURE' THEN 1 ELSE 0 END) AS captures,
                                        SUM(CASE WHEN line_type='REFUND' THEN 1 ELSE 0 END) AS refunds
                                        FROM settlement_lines WHERE batch_id = ?""", (entity_id,))
    return out
