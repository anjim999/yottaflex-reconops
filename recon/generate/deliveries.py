"""Webhook delivery log: how processor events actually arrive, including duplicate deliveries."""
from datetime import timedelta

import numpy as np
import pandas as pd

from ..config import MIX
from ..ids import delivery_id
from .anomalies import label

PAYLOAD = ["event_id", "payment_id", "attempt_id", "event_type", "amount_minor", "currency", "occurred_at"]


def build_deliveries(events: pd.DataFrame, seed: int):
    rng = np.random.default_rng([seed, 7])
    rows = []
    for e in events[PAYLOAD].itertuples(index=False):
        received = e.occurred_at + timedelta(seconds=float(rng.lognormal(np.log(3), 0.8)))
        rows.append({**e._asdict(), "received_at": received, "_dup": False})

    n_dup = int(round(len(events) * MIX["duplicate_webhook_rate"]))
    for i in sorted(rng.choice(len(rows), size=n_dup, replace=False)):
        copies = 2 if rng.random() < MIX["triple_webhook_share"] else 1
        last = rows[i]["received_at"]
        for _ in range(copies):
            last = last + timedelta(seconds=int(rng.integers(30, 6 * 3600)))  # processor retry
            rows.append({**rows[i], "received_at": last, "_dup": True})

    rows.sort(key=lambda r: (r["received_at"], r["event_id"], r["_dup"]))
    gt = []
    for k, r in enumerate(rows, start=1):
        r["delivery_id"] = delivery_id(k)
        if r["_dup"]:
            gt.append(label("DUPLICATE_PROCESSOR_EVENT", "WEBHOOK_DELIVERY", r["delivery_id"], "DUPLICATE_WEBHOOK",
                            "same processor event re-delivered", f"re-delivery of {r['event_id']}"))
    df = pd.DataFrame(rows)
    return df[["delivery_id", "received_at"] + PAYLOAD], gt
