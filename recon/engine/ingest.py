"""Idempotent webhook ingestion: raw deliveries -> canonical processor events."""
import pandas as pd

PAYLOAD = ["payment_id", "attempt_id", "event_type", "amount_minor", "currency", "occurred_at"]


def ingest_deliveries(deliveries: pd.DataFrame, ledger) -> pd.DataFrame:
    d = deliveries.sort_values(["received_at", "delivery_id"]).reset_index(drop=True)
    first = d.drop_duplicates("event_id", keep="first").set_index("event_id")
    dups = d[d.duplicated("event_id", keep="first")]
    for r in dups.itertuples(index=False):
        orig = first.loc[r.event_id]
        same = all(str(getattr(r, c)) == str(orig[c]) for c in PAYLOAD)
        etype = "DUPLICATE_WEBHOOK" if same else "WEBHOOK_PAYLOAD_CONFLICT"
        ledger.exception(etype, "WEBHOOK_DELIVERY", r.delivery_id, f"event {r.event_id}; first delivery {orig.delivery_id}",
                         related=(r.event_id, orig.delivery_id), amount=r.amount_minor, currency=r.currency)
    canonical = first.reset_index()[["event_id"] + PAYLOAD + ["delivery_id", "received_at"]]
    canonical = canonical.rename(columns={"delivery_id": "first_delivery_id", "received_at": "first_received_at"})
    return canonical.sort_values("event_id").reset_index(drop=True)
