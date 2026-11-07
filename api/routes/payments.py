"""Customer / account-holder view: one payment's full timeline across every source."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from ..queries import EXCEPTIONS_LIVE

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("")
def search(request: Request, q: Optional[str] = None, flagged: bool = False, limit: int = Query(25, le=200)):
    db = request.app.state.db
    if flagged:
        return db.all(f"""SELECT p.payment_id, p.merchant_id, p.amount_minor, p.currency, p.status, p.created_at
                          FROM payment_orders p WHERE p.payment_id IN
                          (SELECT entity_id FROM exceptions WHERE entity_type = 'PAYMENT_ORDER')
                          ORDER BY p.payment_id LIMIT ?""", (limit,))
    like = f"%{q or ''}%"
    return db.all("""SELECT payment_id, merchant_id, amount_minor, currency, status, created_at FROM payment_orders
                     WHERE payment_id LIKE ? OR customer_ref LIKE ? OR merchant_id LIKE ?
                     ORDER BY payment_id LIMIT ?""", (like, like, like, limit))


@router.get("/{payment_id}")
def detail(payment_id: str, request: Request):
    db = request.app.state.db
    one = (payment_id,)
    r = db.many({
        "order": ("SELECT * FROM payment_orders WHERE payment_id = ?", one, "one"),
        "merchant": ("SELECT m.* FROM merchants m JOIN payment_orders p ON p.merchant_id = m.merchant_id WHERE p.payment_id = ?", one, "one"),
        "fee_schedules": ("SELECT f.* FROM merchant_fee_schedules f JOIN payment_orders p ON p.merchant_id = f.merchant_id "
                          "WHERE p.payment_id = ? ORDER BY f.version", one),
        "status_history": ("SELECT * FROM order_status_history WHERE payment_id = ? ORDER BY history_id", one),
        "attempts": ("SELECT * FROM payment_attempts WHERE payment_id = ? ORDER BY attempt_id", one),
        "events": ("SELECT * FROM canonical_events WHERE payment_id = ? ORDER BY occurred_at, event_id", one),
        "deliveries": ("SELECT delivery_id, event_id, received_at FROM webhook_deliveries WHERE payment_id = ? ORDER BY received_at", one),
        "settlement_lines": ("SELECT * FROM settlement_lines WHERE payment_id = ? ORDER BY settlement_line_id", one),
        "batches": ("SELECT * FROM settlement_batches WHERE batch_id IN "
                    "(SELECT batch_id FROM settlement_lines WHERE payment_id = ?) ORDER BY batch_id", one),
        "exceptions": (f"SELECT * FROM ({EXCEPTIONS_LIVE}) x WHERE entity_id = ? "
                       "OR entity_id IN (SELECT event_id FROM canonical_events WHERE payment_id = ?) "
                       "OR entity_id IN (SELECT settlement_line_id FROM settlement_lines WHERE payment_id = ?) "
                       "OR entity_id IN (SELECT batch_id FROM settlement_lines WHERE payment_id = ?)", (payment_id,) * 4),
    })
    if not r["order"]:
        raise HTTPException(404, "payment not found")
    return r
