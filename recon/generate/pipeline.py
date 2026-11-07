"""Generation pipeline: master data -> dependent records -> derived values -> labelled anomalies."""
from datetime import date, datetime

import numpy as np
import pandas as pd

from ..config import RULES, SCALES, anomaly_counts, iso_ts, period_for
from ..ids import gt_id
from . import anomalies as A
from .bank import build_bank_lines
from .deliveries import build_deliveries
from .events import generate_attempts_events
from .merchants import generate_merchants
from .orders import generate_orders
from .settlement import build_settlement, recompute_batch_totals
from .status import derive_order_states

INPUT_TABLES = ["merchants", "merchant_fee_schedules", "payment_orders", "order_status_history", "payment_attempts", "processor_events",
                "webhook_deliveries", "settlement_batches", "settlement_lines", "bank_statement_lines"]


def _to_text(df: pd.DataFrame) -> pd.DataFrame:
    """Serialise datetimes/dates to ISO strings exactly as they will be written to disk."""
    out = df.copy()
    for col in out.columns:
        sample = out[col].dropna()
        if sample.empty:
            continue
        v = sample.iloc[0]
        if isinstance(v, (datetime, pd.Timestamp)):
            out[col] = out[col].map(lambda x: iso_ts(x) if isinstance(x, (datetime, pd.Timestamp)) else None)
        elif isinstance(v, date):
            out[col] = out[col].map(lambda x: x.isoformat() if isinstance(x, date) else None)
    return out


def generate(scale_name: str = "starter", seed: int = 20261022) -> dict:
    scale = SCALES[scale_name]
    period = period_for(scale)
    counts = anomaly_counts(scale)
    rng = np.random.default_rng([seed, 6])

    # 1. master data, 2. dependent records (valid parent IDs only)
    merchants, fee_schedules = generate_merchants(scale, seed)
    orders = generate_orders(scale, merchants, seed)
    attempts, events = generate_attempts_events(scale, orders, seed)
    orders, history = derive_order_states(orders, attempts, events)  # derived, before any anomaly
    batches, lines, delayed = build_settlement(events, orders, merchants, fee_schedules, period, seed)

    # 3. labelled anomalies, layer by layer; derived totals recomputed afterwards
    gt, taken = [], set()
    lines, g = A.duplicate_settlement_lines(lines, counts["DUPLICATE_SETTLEMENT_LINE"], rng, taken); gt += g
    lines, g = A.drop_settlement_lines(lines, events, orders, merchants, period,
                                       counts["UNMATCHED_RECORD_DROPPED_LINE"], rng, taken, delayed); gt += g
    lines = lines.sort_values("settlement_line_id").reset_index(drop=True)
    batches = recompute_batch_totals(batches, lines)

    bank, index, normal = build_bank_lines(scale, batches, period, seed, counts["UNMATCHED_RECORD_ORPHAN_BANK"])
    used = set()
    bank, g = A.bank_fee_difference(bank, batches, index, counts["BANK_AMOUNT_DIFFERS_BY_FEE"], rng, used); gt += g
    bank, g = A.bank_currency_mismatch(bank, batches, index, counts["CURRENCY_MISMATCH"], rng, used); gt += g
    bank, g = A.orphan_processor_credits(bank, batches, period, counts["UNMATCHED_RECORD_ORPHAN_BANK"], rng); gt += g

    events, g = A.refund_before_capture(events, lines, counts["REFUND_BEFORE_CAPTURE"], rng); gt += g
    deliveries, g = build_deliveries(events, seed); gt += g

    # normal-but-tricky cases are labelled too, so the engine's decisions can be scored
    for issue, bid, decision in normal:
        gt.append(A.label(issue, "SETTLEMENT_BATCH", bid, None, "baseline variation", "", "NORMAL", decision))
    settled = set(lines.event_id)
    for eid in delayed:
        if eid in settled:
            gt.append(A.label("DELAYED_SETTLEMENT", "PROCESSOR_EVENT", eid, None, "settled 1-3 days late",
                              "", "NORMAL", "MATCHED"))
    ground_truth = pd.DataFrame(gt)
    ground_truth.insert(0, "gt_id", [gt_id(i) for i in range(1, len(ground_truth) + 1)])

    tables = {
        "merchants": merchants, "merchant_fee_schedules": fee_schedules, "payment_orders": orders, "order_status_history": history,
        "payment_attempts": attempts, "processor_events": events, "webhook_deliveries": deliveries,
        "settlement_batches": batches, "settlement_lines": lines, "bank_statement_lines": bank,
    }
    tables = {k: _to_text(v) for k, v in tables.items()}
    run_config = {"scale": scale_name, "seed": seed, "period": period.to_dict(),
                  "rules": RULES.__dict__, "targets": scale.__dict__, "anomaly_counts": counts}
    return {"tables": tables, "ground_truth": ground_truth, "run_config": run_config}
