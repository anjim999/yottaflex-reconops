"""Level 1: processor events <-> settlement lines (plus batch arithmetic)."""
from datetime import timedelta

import pandas as pd

from ..fees import FeeBook

SETTLEABLE = {"payment.captured": "CAPTURE", "payment.refunded": "REFUND"}


def match_events_to_lines(events, lines, batches, orders, merchants, schedules, rules, period, ledger):
    pay_merchant = dict(zip(orders.payment_id, orders.merchant_id))
    mer = merchants.set_index("merchant_id").to_dict("index")
    book = FeeBook(schedules)
    lines = lines.sort_values("settlement_line_id").copy()
    lines["rank"] = lines.groupby("event_id").cumcount()
    first = lines[lines["rank"] == 0].set_index("event_id").to_dict("index")
    ev = events[events.event_type.isin(SETTLEABLE)]
    ev_ids = set(ev.event_id)

    for d in lines[lines["rank"] > 0].itertuples(index=False):
        orig = first[d.event_id]["settlement_line_id"]
        ledger.exception("DUPLICATE_SETTLEMENT_LINE", "SETTLEMENT_LINE", d.settlement_line_id,
                         f"event {d.event_id} already settled on {orig}", (d.event_id, orig, d.batch_id),
                         d.net_minor, d.currency)
    for o in lines[~lines.event_id.isin(ev_ids)].itertuples(index=False):
        ledger.exception("ORPHAN_SETTLEMENT_LINE", "SETTLEMENT_LINE", o.settlement_line_id, "",
                         (o.event_id, o.batch_id), o.net_minor, o.currency)

    grace = timedelta(days=rules.settlement_grace_days)
    for e in ev.itertuples(index=False):
        mid = pay_merchant[e.payment_id]
        m = mer[mid]
        kind = SETTLEABLE[e.event_type]
        ln = first.get(e.event_id)
        if ln is None:
            expected = e.occurred_at.date() + timedelta(days=m["settlement_delay_days"])
            if expected < period.settlement_start:
                ledger.set_status("PROCESSOR_EVENT", e.event_id, "OUT_OF_PERIOD", "expected settlement before period")
            elif expected + grace > period.settlement_end:
                ledger.set_status("PROCESSOR_EVENT", e.event_id, "IN_TRANSIT", "settlement still within grace window")
            else:
                ledger.exception("MISSING_SETTLEMENT_LINE", "PROCESSOR_EVENT", e.event_id,
                                 f"expected by {expected + grace}", (e.payment_id,), e.amount_minor, e.currency)
            continue
        exp_fee = book.fee(mid, e.occurred_at.date(), e.amount_minor) if kind == "CAPTURE" else 0
        exp_net = e.amount_minor - exp_fee if kind == "CAPTURE" else -e.amount_minor
        refs = ([("PROCESSOR_EVENT", e.event_id)], [("SETTLEMENT_LINE", ln["settlement_line_id"])])
        if ln["currency"] != e.currency or ln["gross_minor"] != e.amount_minor or ln["line_type"] != kind:
            ledger.match("EVENT_TO_SETTLEMENT", "PARTIAL", "PARTIAL", "R-SL-01", *refs, e.amount_minor, ln["gross_minor"], e.currency)
            ledger.exception("SETTLEMENT_AMOUNT_MISMATCH", "PROCESSOR_EVENT", e.event_id, "",
                             (ln["settlement_line_id"],), ln["gross_minor"] - e.amount_minor, e.currency)
        elif ln["fee_minor"] != exp_fee or ln["net_minor"] != exp_net:
            ledger.match("EVENT_TO_SETTLEMENT", "PARTIAL", "PARTIAL", "R-SL-01", *refs, exp_net, ln["net_minor"], e.currency)
            ledger.exception("FEE_RULE_VIOLATION", "SETTLEMENT_LINE", ln["settlement_line_id"],
                             f"expected fee {exp_fee}, charged {ln['fee_minor']}", (e.event_id,),
                             ln["fee_minor"] - exp_fee, e.currency)
        else:
            ledger.match("EVENT_TO_SETTLEMENT", "EXACT", "MATCHED", "R-SL-01", *refs, e.amount_minor, ln["gross_minor"], e.currency)
            ledger.set_status("PROCESSOR_EVENT", e.event_id, "MATCHED", "R-SL-01")
            ledger.set_status("SETTLEMENT_LINE", ln["settlement_line_id"], "MATCHED", "R-SL-01")

    _check_batch_arithmetic(lines, batches, ledger)


def _check_batch_arithmetic(lines, batches, ledger):
    g = lines.groupby("batch_id")
    calc = pd.DataFrame({"n": g.size(), "fee": g.fee_minor.sum(), "net": g.net_minor.sum()})
    b = batches.set_index("batch_id").join(calc).fillna(0)
    bad = b[(b.n != b.line_count) | (b.fee != b.fee_minor) | (b.net != b.net_minor)
            | (b.net_minor != b.gross_capture_minor - b.gross_refund_minor - b.fee_minor)]
    for bid, r in bad.iterrows():
        ledger.exception("BATCH_TOTAL_MISMATCH", "SETTLEMENT_BATCH", bid, f"lines net {int(r.net)} vs header {r.net_minor}",
                         amount=int(r.net) - int(r.net_minor), currency=r.currency)
