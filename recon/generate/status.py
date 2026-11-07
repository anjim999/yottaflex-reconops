"""Derive PaymentOrder status + append-only status history from events (never assigned randomly)."""
from collections import defaultdict

import pandas as pd

from ..ids import order_history_id

ORDER_TRANSITIONS = {
    None: {"CREATED"},
    "CREATED": {"AUTHORIZED", "FAILED"},
    "AUTHORIZED": {"CAPTURED", "VOIDED"},
    "CAPTURED": {"PARTIALLY_REFUNDED", "REFUNDED"},
    "PARTIALLY_REFUNDED": {"PARTIALLY_REFUNDED", "REFUNDED"},
    "REFUNDED": set(), "FAILED": set(), "VOIDED": set(),
}


def derive_order_states(orders: pd.DataFrame, attempts: pd.DataFrame, events: pd.DataFrame):
    final_attempt = attempts.groupby("payment_id")["attempt_id"].max().to_dict()
    by_pay = defaultdict(list)
    for e in events.sort_values(["occurred_at", "event_id"]).itertuples(index=False):
        by_pay[e.payment_id].append(e)

    history, out = [], []
    for o in orders.itertuples(index=False):
        status, captured, refunded = "CREATED", 0, 0
        history.append((o.payment_id, None, "CREATED", o.created_at, None))
        for e in by_pay[o.payment_id]:
            new = None
            if e.event_type == "payment.failed" and e.attempt_id == final_attempt[o.payment_id]:
                new = "FAILED"
            elif e.event_type == "payment.authorized":
                new = "AUTHORIZED"
            elif e.event_type == "payment.voided":
                new = "VOIDED"
            elif e.event_type == "payment.captured":
                captured += e.amount_minor
                new = "CAPTURED"
            elif e.event_type == "payment.refunded":
                refunded += e.amount_minor
                new = "REFUNDED" if refunded >= captured else "PARTIALLY_REFUNDED"
            if new:
                if new not in ORDER_TRANSITIONS[status]:
                    raise ValueError(f"illegal transition {status}->{new} for {o.payment_id}")
                history.append((o.payment_id, status, new, e.occurred_at, e.event_id))
                status = new
        last_change = history[-1][3]
        out.append({"status": status, "captured_amount_minor": captured,
                    "refunded_amount_minor": refunded, "updated_at": last_change})

    orders = pd.concat([orders.reset_index(drop=True), pd.DataFrame(out)], axis=1)
    hist = pd.DataFrame(history, columns=["payment_id", "from_status", "to_status", "changed_at", "cause_event_id"])
    hist.insert(0, "history_id", [order_history_id(i) for i in range(1, len(hist) + 1)])
    return orders, hist
