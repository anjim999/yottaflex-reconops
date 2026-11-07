"""Exception workflow: append-only status history + resolution records per actor role.

Analyst / reviewer actions are simulated deterministically (seeded) so the full lifecycle
OPEN -> IN_REVIEW/ESCALATED -> RESOLVED is visible and reproducible. Nothing is overwritten:
the exception's current status is derived from its latest history row.
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from ..config import iso_ts
from ..ids import exception_history_id, resolution_id
from .catalog import EXCEPTIONS

EXCEPTION_TRANSITIONS = {None: {"OPEN"}, "OPEN": {"IN_REVIEW", "ESCALATED", "RESOLVED"},
                         "IN_REVIEW": {"RESOLVED", "ESCALATED"}, "ESCALATED": {"RESOLVED"}, "RESOLVED": set()}
NOTES = {
    "AUTO_DEDUPLICATED": "Later delivery ignored; canonical event unchanged.",
    "RECOVERY_CLAIM_RAISED": "Overpayment recovery claim raised with processor for duplicate line.",
    "PROCESSOR_CLAIM_RAISED": "Claim raised with processor for missing / incorrect settlement.",
    "FEE_ADJUSTMENT_POSTED": "Fee variance booked to fee-adjustment GL account.",
    "TIMESTAMP_INVESTIGATED": "Event ordering investigated; processor clock skew confirmed, no customer impact.",
    "REFUND_REVERSAL_REQUESTED": "Refund reversal requested pending investigation.",
    "FX_RETURN_REQUESTED": "Payout in wrong currency returned to processor for re-issue.",
    "SUSPENSE_POSTED": "Unidentified credit posted to suspense account.",
    "LATE_PAYOUT_ACCEPTED": "Late payout accepted after confirming value date with bank.",
    "MANUAL_REVIEW": "Reviewed manually and corrected.",
}


def apply_workflow(exceptions: pd.DataFrame, run_at: datetime, seed: int):
    rng = np.random.default_rng([seed, 99])
    hist, res, status = [], [], []

    def move(xid, frm, to, at, actor):
        assert to in EXCEPTION_TRANSITIONS[frm]
        hist.append({"history_id": exception_history_id(len(hist) + 1), "exception_id": xid,
                     "from_status": frm, "to_status": to, "changed_at": iso_ts(at), "actor_role": actor})
        return to

    for x in exceptions.itertuples(index=False):
        _, owner, action, _, _ = EXCEPTIONS[x.exception_type]
        t = run_at
        s = move(x.exception_id, None, "OPEN", t, "SYSTEM")
        resolver = None
        if owner == "SYSTEM":
            resolver = "SYSTEM"
        elif owner == "RISK_REVIEWER":
            t += timedelta(hours=float(rng.uniform(1, 4)))
            s = move(x.exception_id, s, "ESCALATED", t, "OPS_ANALYST")
            if rng.random() < 0.5:
                t += timedelta(hours=float(rng.uniform(24, 120)))
                resolver = "RISK_REVIEWER"
        else:
            if rng.random() < 0.6:
                t += timedelta(hours=float(rng.uniform(0.5, 8)))
                s = move(x.exception_id, s, "IN_REVIEW", t, "OPS_ANALYST")
                t += timedelta(hours=float(rng.uniform(1, 72)))
                resolver = "OPS_ANALYST"
        if resolver:
            s = move(x.exception_id, s, "RESOLVED", t, resolver)
            amount = x.amount_minor if pd.notna(x.amount_minor) else 0
            adj = -amount if x.exception_type == "DUPLICATE_SETTLEMENT_LINE" else amount
            res.append({"resolution_id": resolution_id(len(res) + 1), "exception_id": x.exception_id,
                        "resolution_type": action, "resolved_by_role": resolver, "resolved_at": iso_ts(t),
                        "adjustment_amount_minor": int(adj) if action != "AUTO_DEDUPLICATED" else 0,
                        "currency": x.currency, "notes": NOTES[action]})
        status.append(s)

    out = exceptions.copy()
    out["status"] = status  # derived from the latest history row, never edited in place
    return out, pd.DataFrame(hist), pd.DataFrame(res)
