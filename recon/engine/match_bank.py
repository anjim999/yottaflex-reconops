"""Level 2: settlement batches <-> bank statement lines (reference, amount, currency, date window)."""
from datetime import timedelta

import numpy as np

from ..config import CURRENCIES, PROCESSOR_NAME

REF_PATTERN = r"(SET-\d{4}-\d{6})"


def match_batches_to_bank(batches, bank, rules, period, ledger):
    tol, win = rules.amount_tolerance_minor, timedelta(days=rules.date_window_days)
    bank = bank.copy()
    bank["signed"] = np.where(bank.direction == "CREDIT", bank.amount_minor, -bank.amount_minor)
    bank["batch_ref"] = bank.reference.fillna("").str.extract(REF_PATTERN)[0]
    scoped_mask = (bank.counterparty == PROCESSOR_NAME) | bank.batch_ref.notna()
    for bid in bank.loc[~scoped_mask, "bank_line_id"]:
        ledger.set_status("BANK_LINE", bid, "OUT_OF_SCOPE", "R-BK-00 non-processor activity")
    scoped = bank[scoped_mask].sort_values("bank_line_id")
    by_ref = {ref: g for ref, g in scoped[scoped.batch_ref.notna()].groupby("batch_ref")}
    handled = set()

    for b in batches.sort_values("batch_id").itertuples(index=False):
        grp = by_ref.get(b.batch_id)
        if grp is None:
            continue
        handled.add(b.batch_id)
        ids = list(grp.bank_line_id)
        left, right = [("SETTLEMENT_BATCH", b.batch_id)], [("BANK_LINE", i) for i in ids]
        total, diff = int(grp.signed.sum()), int(grp.signed.sum()) - int(b.net_minor)
        if (grp.currency != b.currency).any():
            ledger.exception("CURRENCY_MISMATCH", "SETTLEMENT_BATCH", b.batch_id,
                             f"batch {b.currency}, bank {','.join(sorted(set(grp.currency)))}", ids, b.net_minor, b.currency)
            _mark(ledger, ids, "EXCEPTION", "CURRENCY_MISMATCH")
            continue
        late = ((grp.value_date < b.settlement_date) | (grp.value_date > b.settlement_date + win)).any()
        if abs(diff) <= tol and not late:
            mtype = "SPLIT" if len(ids) > 1 else ("EXACT" if diff == 0 else "WITHIN_TOLERANCE")
            ledger.match("BATCH_TO_BANK", mtype, "MATCHED", "R-BK-01", left, right, b.net_minor, total, b.currency)
            ledger.set_status("SETTLEMENT_BATCH", b.batch_id, "MATCHED", f"R-BK-01 {mtype}")
            _mark(ledger, ids, "MATCHED", "R-BK-01")
            continue
        ledger.match("BATCH_TO_BANK", "PARTIAL", "PARTIAL", "R-BK-01", left, right, b.net_minor, total, b.currency)
        _mark(ledger, ids, "PARTIAL", "R-BK-01 partial")
        if abs(diff) <= tol:
            ledger.exception("PAYOUT_OUTSIDE_DATE_WINDOW", "SETTLEMENT_BATCH", b.batch_id,
                             f"window {b.settlement_date}+{rules.date_window_days}d", ids, b.net_minor, b.currency)
        elif diff == b.fee_minor or diff == -CURRENCIES[b.currency].wire_fee_minor:
            why = "fees not deducted" if diff == b.fee_minor else "bank wire fee deducted"
            ledger.exception("FEE_DIFFERENCE", "SETTLEMENT_BATCH", b.batch_id, f"{why}; diff {diff}", ids, diff, b.currency)
        else:
            ledger.exception("BANK_AMOUNT_MISMATCH", "SETTLEMENT_BATCH", b.batch_id, f"diff {diff}", ids, diff, b.currency)

    known = set(batches.batch_id)
    for ref, grp in by_ref.items():
        if ref not in known:
            for i in grp.bank_line_id:
                ledger.exception("UNMATCHED_BANK_LINE", "BANK_LINE", i, f"unknown batch reference {ref}")

    # Fuzzy pass for reference-less processor credits: currency + amount tolerance + date window, unique only.
    open_b = batches[~batches.batch_id.isin(handled)]
    for ln in scoped[scoped.batch_ref.isna()].itertuples(index=False):
        c = open_b[(open_b.currency == ln.currency) & ((open_b.net_minor - ln.signed).abs() <= tol)
                   & (open_b.settlement_date <= ln.value_date) & (open_b.settlement_date + win >= ln.value_date)]
        if len(c) == 1:
            b = c.iloc[0]
            mtype = "FUZZY"
            ledger.match("BATCH_TO_BANK", mtype, "MATCHED", "R-BK-05F", [("SETTLEMENT_BATCH", b.batch_id)],
                         [("BANK_LINE", ln.bank_line_id)], b.net_minor, ln.signed, b.currency)
            ledger.set_status("SETTLEMENT_BATCH", b.batch_id, "MATCHED", "R-BK-05F FUZZY")
            ledger.set_status("BANK_LINE", ln.bank_line_id, "MATCHED", "R-BK-05F")
            handled.add(b.batch_id)
            open_b = open_b[open_b.batch_id != b.batch_id]
        elif len(c) > 1:
            ledger.exception("AMBIGUOUS_BANK_MATCH", "BANK_LINE", ln.bank_line_id, f"{len(c)} candidate batches",
                             tuple(c.batch_id), ln.signed, ln.currency)
        else:
            ledger.exception("UNMATCHED_BANK_LINE", "BANK_LINE", ln.bank_line_id, "no batch fits amount/currency/date",
                             amount=ln.signed, currency=ln.currency)

    for b in batches[~batches.batch_id.isin(handled)].itertuples(index=False):
        if b.settlement_date + win > period.statement_end:
            ledger.set_status("SETTLEMENT_BATCH", b.batch_id, "IN_TRANSIT", "payout window extends past statement")
        else:
            ledger.exception("UNMATCHED_SETTLEMENT_BATCH", "SETTLEMENT_BATCH", b.batch_id, "", amount=b.net_minor,
                             currency=b.currency)


def _mark(ledger, ids, status, reason):
    for i in ids:
        ledger.set_status("BANK_LINE", i, status, reason)
