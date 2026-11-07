"""Lifecycle checks on canonical events: orphan references, refund ordering, over-refunds."""
import pandas as pd


def check_lifecycle(events: pd.DataFrame, orders: pd.DataFrame, attempts: pd.DataFrame, ledger):
    known_pay, known_att = set(orders.payment_id), set(attempts.attempt_id)
    for e in events[~events.payment_id.isin(known_pay) | ~events.attempt_id.isin(known_att)].itertuples():
        ledger.exception("ORPHAN_EVENT", "PROCESSOR_EVENT", e.event_id, f"payment {e.payment_id}")

    cap = events[events.event_type == "payment.captured"].groupby("payment_id").agg(
        cap_at=("occurred_at", "min"), cap_amt=("amount_minor", "sum"), cap_id=("event_id", "first"))
    ref = events[events.event_type == "payment.refunded"].groupby("payment_id").agg(
        ref_at=("occurred_at", "min"), ref_amt=("amount_minor", "sum"), ref_ids=("event_id", "|".join), ccy=("currency", "first"))
    j = ref.join(cap, how="left").sort_index()
    for pid, r in j.iterrows():
        related = tuple(r.ref_ids.split("|"))
        if pd.isna(r.cap_at):
            ledger.exception("REFUND_WITHOUT_CAPTURE", "PAYMENT_ORDER", pid, "", related, r.ref_amt, r.ccy)
            continue
        if r.ref_at < r.cap_at:
            ledger.exception("REFUND_BEFORE_CAPTURE", "PAYMENT_ORDER", pid,
                             f"refund at {r.ref_at:%Y-%m-%d %H:%M}, capture at {r.cap_at:%Y-%m-%d %H:%M}",
                             related + (r.cap_id,), r.ref_amt, r.ccy)
        if r.ref_amt > r.cap_amt:
            ledger.exception("OVER_REFUND", "PAYMENT_ORDER", pid, f"refunded {r.ref_amt} > captured {r.cap_amt}",
                             related, r.ref_amt - r.cap_amt, r.ccy)
