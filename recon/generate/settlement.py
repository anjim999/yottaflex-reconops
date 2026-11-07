"""Step 3: aggregate captured/refunded events into settlement batches with fees.

One batch per (currency, settlement_date). Batch totals are always *derived* from lines.
"""
from collections import defaultdict
from datetime import datetime, time, timedelta

import numpy as np
import pandas as pd

from ..config import CURRENCY_CODES, MIX, PROCESSOR_CODE, UTC
from ..ids import batch_id, line_id
from ..fees import FeeBook

SETTLEABLE = {"payment.captured": "CAPTURE", "payment.refunded": "REFUND"}


def build_settlement(events, orders, merchants, schedules, period, seed: int):
    rng = np.random.default_rng([seed, 4])
    pay_merchant = dict(zip(orders["payment_id"], orders["merchant_id"]))
    mer = merchants.set_index("merchant_id").to_dict("index")
    book = FeeBook(schedules)

    grouped, delayed = defaultdict(list), []
    for e in events[events["event_type"].isin(SETTLEABLE)].itertuples(index=False):
        mid = pay_merchant[e.payment_id]
        m = mer[mid]
        extra = 0
        if rng.random() < MIX["delayed_settlement_rate"]:
            extra = int(rng.integers(1, MIX["max_extra_settlement_delay"] + 1))
        sdate = e.occurred_at.date() + timedelta(days=m["settlement_delay_days"] + extra)
        if not (period.settlement_start <= sdate <= period.settlement_end):
            continue  # settled in a prior cycle or still in transit at period end
        if extra:
            delayed.append(e.event_id)
        kind = SETTLEABLE[e.event_type]
        gross = int(e.amount_minor)
        fee = book.fee(mid, e.occurred_at.date(), gross) if kind == "CAPTURE" else 0
        grouped[(sdate, CURRENCY_CODES.index(e.currency))].append({
            "event_id": e.event_id, "payment_id": e.payment_id, "merchant_id": mid, "line_type": kind,
            "gross_minor": gross, "fee_minor": fee,
            "net_minor": gross - fee if kind == "CAPTURE" else -gross,
            "currency": e.currency, "_occ": e.occurred_at,
        })

    batches, lines = [], []
    for k, key in enumerate(sorted(grouped), start=1):
        sdate, ci = key
        bid = batch_id(k)
        for j, ln in enumerate(sorted(grouped[key], key=lambda r: (r["_occ"], r["event_id"])), start=1):
            ln.pop("_occ")
            lines.append({"settlement_line_id": line_id(bid, j), "batch_id": bid, **ln})
        batches.append({"batch_id": bid, "processor": PROCESSOR_CODE, "currency": CURRENCY_CODES[ci],
                        "settlement_date": sdate, "status": "CLOSED",
                        "created_at": datetime.combine(sdate, time(2, 0), tzinfo=UTC)})
    batches = recompute_batch_totals(pd.DataFrame(batches), pd.DataFrame(lines))
    return batches, pd.DataFrame(lines), delayed


def recompute_batch_totals(batches: pd.DataFrame, lines: pd.DataFrame) -> pd.DataFrame:
    """Derive batch totals from its lines: net = captured - refunded - fees."""
    b = batches.drop(columns=[c for c in ["line_count", "gross_capture_minor", "gross_refund_minor",
                                          "fee_minor", "net_minor"] if c in batches.columns])
    cap = lines[lines.line_type == "CAPTURE"].groupby("batch_id")["gross_minor"].sum()
    ref = lines[lines.line_type == "REFUND"].groupby("batch_id")["gross_minor"].sum()
    g = lines.groupby("batch_id")
    b["line_count"] = b.batch_id.map(g.size()).fillna(0).astype(int)
    b["gross_capture_minor"] = b.batch_id.map(cap).fillna(0).astype(int)
    b["gross_refund_minor"] = b.batch_id.map(ref).fillna(0).astype(int)
    b["fee_minor"] = b.batch_id.map(g["fee_minor"].sum()).fillna(0).astype(int)
    b["net_minor"] = b.batch_id.map(g["net_minor"].sum()).fillna(0).astype(int)
    assert (b.net_minor == b.gross_capture_minor - b.gross_refund_minor - b.fee_minor).all()
    return b
