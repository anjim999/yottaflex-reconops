"""Step 4: bank statement lines - processor payouts plus realistic unrelated account activity."""
from datetime import timedelta

import numpy as np
import pandas as pd

from ..config import CURRENCIES, CURRENCY_CODES, MIX, PROCESSOR_NAME, RULES
from ..ids import bank_line_id

VENDORS = ["CLOUDHOST INC", "OFFICEWORKS", "ACME LOGISTICS", "DATAGRID SAAS", "METRO UTILITIES",
           "LEGAL PARTNERS LLP", "ADSPHERE MEDIA", "SECURENET AUDIT"]
CUSTOMERS = ["WHOLESALE CLIENT A", "WHOLESALE CLIENT B", "INVOICE PAYER", "PARTNER REBATE"]
NOISE = [  # weight, direction, transaction_code, counterparties, description, median USD
    (0.35, "DEBIT", "DEBIT_TRANSFER", VENDORS, "VENDOR PAYMENT", 2500),
    (0.10, "DEBIT", "DEBIT_TRANSFER", ["PAYROLL SERVICES"], "PAYROLL", 40000),
    (0.25, "CREDIT", "CREDIT_TRANSFER", CUSTOMERS, "INBOUND TRANSFER", 1500),
    (0.20, "DEBIT", "BANK_CHARGE", ["FIRST LEDGER BANK"], "ACCOUNT MAINTENANCE FEE", 25),
    (0.10, "CREDIT", "INTEREST", ["FIRST LEDGER BANK"], "CREDIT INTEREST", 120),
]


def account_for(ccy: str) -> str:
    return f"ACC-{ccy}-001"


def payout_reference(bid: str) -> str:
    return f"NOVAPAY PAYOUT {bid}"


def _line(vdate, direction, amount, ccy, cp, ref, desc, code):
    return {"account_id": account_for(ccy), "value_date": vdate, "booking_date": vdate, "direction": direction,
            "amount_minor": int(amount), "currency": ccy, "counterparty": cp, "reference": ref,
            "description": desc, "transaction_code": code}


def _fuzzy_unique(b, amount, vdate, batches) -> bool:
    """A reference-less payout is only realistic to auto-match if exactly one batch fits."""
    tol, win = RULES.amount_tolerance_minor, timedelta(days=RULES.date_window_days)
    c = batches[(batches.currency == b.currency) & ((batches.net_minor - amount).abs() <= tol)
                & (batches.settlement_date <= vdate) & (batches.settlement_date >= vdate - win)]
    return len(c) == 1


def build_bank_lines(scale, batches: pd.DataFrame, period, seed: int, reserved: int):
    """Returns (bank_lines, payout_index, normal_labels).

    payout_index: batch_id -> (kind, [row positions]) used only by the anomaly injector.
    """
    rng = np.random.default_rng([seed, 5])
    rows, index, labels = [], {}, []
    for b in batches.itertuples(index=False):
        vdate = b.settlement_date + timedelta(days=int(rng.choice(3, p=MIX["bank_lag_probs"])))
        net, ref = int(b.net_minor), payout_reference(b.batch_id)
        direction = "CREDIT" if net >= 0 else "DEBIT"
        r = rng.random()
        if r < MIX["split_payout_rate"] and net > 1:
            part = int(net * rng.uniform(0.3, 0.7))
            index[b.batch_id] = ("SPLIT", [len(rows), len(rows) + 1])
            rows.append(_line(vdate, direction, part, b.currency, PROCESSOR_NAME, ref, "PAYOUT PART 1/2", "CREDIT_TRANSFER"))
            rows.append(_line(vdate, direction, net - part, b.currency, PROCESSOR_NAME, ref, "PAYOUT PART 2/2", "CREDIT_TRANSFER"))
            labels.append(("SPLIT_PAYOUT", b.batch_id, "MATCHED_SPLIT"))
            continue
        kind, amount, line_ref = "EXACT", abs(net), ref
        r -= MIX["split_payout_rate"]
        if r < MIX["rounding_rate"]:
            kind, amount = "ROUNDING", abs(net) + int(rng.choice([-1, 1]))
            labels.append(("ROUNDING_DIFFERENCE", b.batch_id, "MATCHED_WITHIN_TOLERANCE"))
        elif r < MIX["rounding_rate"] + MIX["missing_reference_rate"] and _fuzzy_unique(b, net, vdate, batches):
            kind, line_ref = "FUZZY", None
            labels.append(("MISSING_BANK_REFERENCE", b.batch_id, "MATCHED_FUZZY"))
        index[b.batch_id] = (kind, [len(rows)])
        rows.append(_line(vdate, direction, amount, b.currency, PROCESSOR_NAME, line_ref, "NOVAPAY PAYOUT", "CREDIT_TRANSFER"))

    n_noise = scale.bank_lines - len(rows) - reserved
    if n_noise < 0:
        raise ValueError("bank_lines target too small for payouts")
    days = (period.statement_end - period.settlement_start).days + 1
    weights = np.array([w for w, *_ in NOISE])
    shares = np.array([c.volume_share for c in CURRENCIES.values()])
    for _ in range(n_noise):
        w, direction, code, cps, desc, median = NOISE[rng.choice(len(NOISE), p=weights)]
        cur = CURRENCIES[str(rng.choice(CURRENCY_CODES, p=shares))]
        amount = max(1, int(rng.lognormal(np.log(median), 0.6) * cur.fx_per_usd * 10 ** cur.exponent))
        ref = f"INV-{int(rng.integers(10000, 99999))}" if desc == "VENDOR PAYMENT" else None
        vdate = period.settlement_start + timedelta(days=int(rng.integers(days)))
        rows.append(_line(vdate, direction, amount, cur.code, str(rng.choice(cps)), ref, desc, code))

    # Chronological IDs; payout_index positions are remapped to the final IDs.
    order = sorted(range(len(rows)), key=lambda i: (rows[i]["value_date"], rows[i]["account_id"], i))
    pos_to_id = {}
    for k, i in enumerate(order, start=1):
        pos_to_id[i] = bank_line_id(k)
    bank = pd.DataFrame([{"bank_line_id": pos_to_id[i], **rows[i]} for i in order])
    index = {bid: (kind, [pos_to_id[p] for p in pos]) for bid, (kind, pos) in index.items()}
    return bank, index, labels
