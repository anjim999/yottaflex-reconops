"""Step 5: inject labelled edge cases into otherwise valid baseline data.

Each injector touches only its target rows and returns ground-truth labels describing
exactly what was changed and which decision the engine is expected to make.
"""
from datetime import timedelta

import numpy as np
import pandas as pd

from ..config import CURRENCIES, CURRENCY_CODES, PROCESSOR_NAME, RULES
from ..ids import bank_line_id, line_id
from .bank import account_for

ISSUE_TO_EXCEPTION = {
    "DUPLICATE_SETTLEMENT_LINE": "DUPLICATE_SETTLEMENT_LINE",
    "BANK_AMOUNT_DIFFERS_BY_FEE": "FEE_DIFFERENCE",
    "REFUND_BEFORE_CAPTURE": "REFUND_BEFORE_CAPTURE",
    "UNMATCHED_RECORD_DROPPED": None,  # depends on variant
    "CURRENCY_MISMATCH": "CURRENCY_MISMATCH",
    "DUPLICATE_PROCESSOR_EVENT": "DUPLICATE_WEBHOOK",
}


def label(issue, entity_type, entity_id, expected_exception, rule, detail, category="ANOMALY", decision=None):
    return {"issue_type": issue, "category": category, "entity_type": entity_type, "entity_id": entity_id,
            "expected_exception_type": expected_exception,
            "expected_decision": decision or ("RAISE_EXCEPTION" if expected_exception else "NO_EXCEPTION"),
            "injection_rule": rule, "detail": detail}


def _pick(rng, candidates, k):
    candidates = sorted(candidates)
    k = min(k, len(candidates))
    return [candidates[i] for i in sorted(rng.choice(len(candidates), size=k, replace=False))]


def duplicate_settlement_lines(lines, k, rng, taken):
    """Processor file repeats a capture line inside the same batch (new line number, same event)."""
    cands = set(lines.loc[lines.line_type == "CAPTURE", "settlement_line_id"]) - taken
    chosen = _pick(rng, cands, k)
    next_no = lines.groupby("batch_id")["settlement_line_id"].max().str[-3:].astype(int).to_dict()
    src = lines.set_index("settlement_line_id")
    new_rows, gt = [], []
    for sid in chosen:
        row = src.loc[sid].to_dict()
        next_no[row["batch_id"]] += 1
        nid = line_id(row["batch_id"], next_no[row["batch_id"]])
        new_rows.append({"settlement_line_id": nid, **row})
        taken.add(row["event_id"])
        gt.append(label("DUPLICATE_SETTLEMENT_LINE", "SETTLEMENT_LINE", nid, "DUPLICATE_SETTLEMENT_LINE",
                        "copy of capture line appended to same batch", f"duplicate of {sid}"))
    return pd.concat([lines, pd.DataFrame(new_rows)], ignore_index=True), gt


def drop_settlement_lines(lines, events, orders, merchants, period, k, rng, taken, delayed):
    """Processor silently omits a capture that should have settled well inside the period."""
    delay = orders.set_index("payment_id")["merchant_id"].map(
        merchants.set_index("merchant_id")["settlement_delay_days"])
    ev = events[events.event_type == "payment.captured"].copy()
    ev["expected"] = [o.date() + timedelta(days=int(delay[p])) for o, p in zip(ev.occurred_at, ev.payment_id)]
    grace = timedelta(days=RULES.settlement_grace_days)
    ok = (ev.expected >= period.settlement_start) & (ev.expected + grace <= period.settlement_end)
    with_line = set(lines.event_id)
    cands = {e for e in ev.loc[ok, "event_id"] if e in with_line} - taken - set(delayed)
    chosen = _pick(rng, cands, k)
    taken.update(chosen)
    gt = [label("UNMATCHED_RECORD_DROPPED", "PROCESSOR_EVENT", e, "MISSING_SETTLEMENT_LINE",
                "capture line removed from settlement file", "capture never settled; must not be silently dropped")
          for e in chosen]
    return lines[~lines.event_id.isin(chosen)].reset_index(drop=True), gt


def bank_fee_difference(bank, batches, index, k, rng, used):
    """Bank credit differs from batch net by a fee: fees not deducted, or bank wire fee taken."""
    b = batches.set_index("batch_id")
    cands = {bid for bid, (kind, _) in index.items() if kind == "EXACT" and b.loc[bid, "net_minor"] > 0} - used
    gt = []
    for i, bid in enumerate(_pick(rng, cands, k)):
        used.add(bid)
        bank_id = index[bid][1][0]
        row = b.loc[bid]
        if i % 2 == 0:
            delta, why = int(row.fee_minor), "processor fees not deducted (bank = gross of fees)"
        else:
            delta, why = -CURRENCIES[row.currency].wire_fee_minor, "bank deducted incoming wire fee"
        bank.loc[bank.bank_line_id == bank_id, "amount_minor"] += delta
        gt.append(label("BANK_AMOUNT_DIFFERS_BY_FEE", "SETTLEMENT_BATCH", bid, "FEE_DIFFERENCE",
                        why, f"{bank_id} differs by {delta} minor units"))
    return bank, gt


def bank_currency_mismatch(bank, batches, index, k, rng, used):
    cands = {bid for bid, (kind, _) in index.items() if kind == "EXACT"} - used
    ccy = batches.set_index("batch_id")["currency"]
    gt = []
    for bid in _pick(rng, cands, k):
        used.add(bid)
        bank_id = index[bid][1][0]
        wrong = CURRENCY_CODES[(CURRENCY_CODES.index(ccy[bid]) + 1) % len(CURRENCY_CODES)]
        bank.loc[bank.bank_line_id == bank_id, "currency"] = wrong
        gt.append(label("CURRENCY_MISMATCH", "SETTLEMENT_BATCH", bid, "CURRENCY_MISMATCH",
                        "payout booked in wrong currency", f"{bank_id}: expected {ccy[bid]}, got {wrong}"))
    return bank, gt


def orphan_processor_credits(bank, batches, period, k, rng):
    """Processor credit with no usable reference and no matching batch amount."""
    start = int(bank.bank_line_id.str[-6:].astype(int).max())
    days = (period.statement_end - period.settlement_start).days + 1
    rows, gt = [], []
    for j in range(k):
        ccy = CURRENCY_CODES[j % len(CURRENCY_CODES)]
        nets = set(batches.loc[batches.currency == ccy, "net_minor"])
        amount = int(rng.integers(10_000, 5_000_000))
        while any(abs(amount - n) <= RULES.amount_tolerance_minor for n in nets):
            amount += 7
        bid = bank_line_id(start + j + 1)
        vdate = period.settlement_start + timedelta(days=int(rng.integers(days)))
        rows.append({"bank_line_id": bid, "account_id": account_for(ccy), "value_date": vdate,
                     "booking_date": vdate, "direction": "CREDIT", "amount_minor": amount, "currency": ccy,
                     "counterparty": PROCESSOR_NAME, "reference": None, "description": "NOVAPAY PAYOUT",
                     "transaction_code": "CREDIT_TRANSFER"})
        gt.append(label("UNMATCHED_RECORD_DROPPED", "BANK_LINE", bid, "UNMATCHED_BANK_LINE",
                        "processor credit with no settlement batch", "must surface, not be silently dropped"))
    return pd.concat([bank, pd.DataFrame(rows)], ignore_index=True), gt


def refund_before_capture(events, lines, k, rng):
    """Refund event timestamp moved before its payment's capture (clock skew / bad feed)."""
    ev = events.copy()
    settled = set(lines.event_id)
    refunds = ev[(ev.event_type == "payment.refunded") & ev.event_id.isin(settled)]
    refunds = refunds[~refunds.payment_id.duplicated(keep=False)]
    cap_at = ev[ev.event_type == "payment.captured"].set_index("payment_id")["occurred_at"]
    gt = []
    for eid in _pick(rng, set(refunds.event_id), k):
        i = ev.index[ev.event_id == eid][0]
        pid = ev.at[i, "payment_id"]
        ev.at[i, "occurred_at"] = cap_at[pid] - timedelta(seconds=int(rng.integers(60, 3 * 86_400)))
        gt.append(label("REFUND_BEFORE_CAPTURE", "PAYMENT_ORDER", pid, "REFUND_BEFORE_CAPTURE",
                        "refund occurred_at set before capture occurred_at", f"refund event {eid}"))
    return ev, gt
