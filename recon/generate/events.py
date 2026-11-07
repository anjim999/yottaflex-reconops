"""Step 2b: PaymentAttempts and the processor's canonical event registry."""
from datetime import datetime, time, timedelta

import numpy as np
import pandas as pd

from ..config import MIX, PROCESSOR_CODE, START_DATE, UTC
from ..ids import attempt_id, event_id

FAILURE_CODES = ["insufficient_funds", "do_not_honor", "expired_card", "card_declined",
                 "processing_error", "authentication_failed"]
TYPE_RANK = {"payment.failed": 0, "payment.authorized": 1, "payment.voided": 2,
             "payment.captured": 3, "payment.refunded": 4}


def generate_attempts_events(scale, orders: pd.DataFrame, seed: int):
    rng = np.random.default_rng([seed, 3])
    n = len(orders)
    extra = max(0, scale.attempts - n)
    retry = set(rng.choice(n, size=min(extra, n), replace=False).tolist())
    period_end = datetime.combine(START_DATE + timedelta(days=scale.settlement_days), time(0), tzinfo=UTC)
    secs = lambda lo, hi: timedelta(seconds=int(rng.integers(lo, hi)))
    hours = lambda lo, hi: timedelta(hours=float(rng.uniform(lo, hi)))

    attempts, events = [], []
    for i, o in enumerate(orders.itertuples(index=False)):
        n_att = 2 if i in retry else 1
        final_fail = rng.random() < MIX["final_fail_rate"]
        t = o.created_at
        for a in range(1, n_att + 1):
            t = t + (secs(5, 120) if a == 1 else secs(60, 1800))
            aid = attempt_id(o.payment_id, a)
            failed = a < n_att or final_fail
            attempts.append({
                "attempt_id": aid, "payment_id": o.payment_id, "attempt_no": a, "created_at": t,
                "status": "FAILED" if failed else "SUCCEEDED",
                "failure_code": str(rng.choice(FAILURE_CODES)) if failed else None,
                "processor": PROCESSOR_CODE,
            })
            base = {"payment_id": o.payment_id, "attempt_id": aid, "currency": o.currency}
            if failed:
                events.append({**base, "event_type": "payment.failed", "amount_minor": o.amount_minor,
                               "occurred_at": t + secs(1, 6)})
                continue
            auth_t = t + secs(1, 6)
            events.append({**base, "event_type": "payment.authorized", "amount_minor": o.amount_minor,
                           "occurred_at": auth_t})
            if rng.random() < MIX["void_rate"]:
                events.append({**base, "event_type": "payment.voided", "amount_minor": o.amount_minor,
                               "occurred_at": auth_t + hours(1, 48)})
                continue
            delayed = rng.random() < MIX["delayed_capture_share"]
            cap_t = auth_t + (hours(1, 48) if delayed else secs(1, 60))
            events.append({**base, "event_type": "payment.captured", "amount_minor": o.amount_minor,
                           "occurred_at": cap_t})
            if rng.random() < MIX["refund_rate"]:
                ref_t = cap_t + hours(24, 24 * 20)
                partial = rng.random() < MIX["partial_refund_share"]
                amt = int(o.amount_minor * rng.uniform(0.1, 0.9)) if partial else o.amount_minor
                if ref_t < period_end and amt > 0:
                    events.append({**base, "event_type": "payment.refunded", "amount_minor": amt,
                                   "occurred_at": ref_t})

    events.sort(key=lambda e: (e["occurred_at"], e["payment_id"], TYPE_RANK[e["event_type"]]))
    for k, e in enumerate(events, start=1):
        e["event_id"] = event_id(k)
    cols = ["event_id", "payment_id", "attempt_id", "event_type", "amount_minor", "currency", "occurred_at"]
    return pd.DataFrame(attempts), pd.DataFrame(events)[cols]
