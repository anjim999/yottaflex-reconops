"""Data profile: evidence that distributions are realistic and varied (rubric item a)."""
import pandas as pd

from .money import to_major
from .reports import md_table


def _q(s: pd.Series) -> dict:
    return {"min": s.min(), "p05": s.quantile(.05), "p50": s.median(), "mean": s.mean(), "p95": s.quantile(.95), "max": s.max()}


def profile(t: dict) -> dict:
    o, a, e, sl, sb, bk, m, fs = (t[k] for k in ["payment_orders", "payment_attempts", "processor_events", "settlement_lines",
                                                  "settlement_batches", "bank_statement_lines", "merchants", "merchant_fee_schedules"])
    out = {}
    amt = o.assign(major=[to_major(int(v), c) for v, c in zip(o.amount_minor, o.currency)])
    out["order_amount_by_currency_major_units"] = pd.DataFrame(
        {c: _q(g.major) for c, g in amt.groupby("currency")}).T.round(2).reset_index(names="currency")
    vol = o.merchant_id.value_counts()
    out["merchant_concentration"] = pd.DataFrame([{
        "merchants_with_orders": len(vol), "orders_top_1pct_merchants_share": round(vol.head(max(1, len(vol) // 100)).sum() / len(o), 3),
        "orders_top_10pct_merchants_share": round(vol.head(max(1, len(vol) // 10)).sum() / len(o), 3),
        "median_orders_per_merchant": int(vol.median()), "max_orders_per_merchant": int(vol.max())}])
    out["currency_mix"] = o.currency.value_counts(normalize=True).round(3).rename("share").reset_index()
    out["payment_method_mix"] = o.payment_method.value_counts(normalize=True).round(3).rename("share").reset_index()
    out["order_status_mix"] = o.status.value_counts(normalize=True).round(4).rename("share").reset_index()
    out["attempts_per_order"] = a.groupby("payment_id").size().value_counts().sort_index().rename("orders").rename_axis("attempts").reset_index()
    out["failure_codes"] = a.failure_code.value_counts().rename("attempts").reset_index()
    out["event_type_mix"] = e.event_type.value_counts().rename("events").reset_index()

    ref = e[e.event_type == "payment.refunded"].set_index("payment_id").amount_minor
    cap = e[e.event_type == "payment.captured"].set_index("payment_id").amount_minor
    ratio = (ref / cap.reindex(ref.index))
    out["refunds"] = pd.DataFrame([{"refund_rate_of_captures": round(len(ref) / max(len(cap), 1), 4),
                                    "partial_refund_share": round((ratio < 1).mean(), 3),
                                    "median_partial_refund_ratio": round(ratio[ratio < 1].median(), 3)}])
    ev = e.set_index("event_id")
    occ = pd.to_datetime(ev.occurred_at.reindex(sl.event_id).values, utc=True).normalize().tz_localize(None)
    lag = (pd.to_datetime(sl.batch_id.map(sb.set_index("batch_id").settlement_date)).values - occ.values).astype("timedelta64[D]").astype(int)
    out["capture_to_settlement_days"] = pd.Series(lag).value_counts().sort_index().rename("lines").rename_axis("days").reset_index()
    eff = sl[sl.line_type == "CAPTURE"]
    out["fees"] = pd.DataFrame([{"effective_fee_rate_pct": round(100 * eff.fee_minor.sum() / eff.gross_minor.sum(), 3),
                                 "merchants_repriced_mid_period": int((fs.version > 1).sum()),
                                 "risk_tier_mix": m.risk_tier.value_counts().to_dict()}])
    out["lines_per_batch"] = pd.DataFrame([_q(sb.line_count)]).round(1)
    out["bank_lines_by_type"] = bk.groupby(["transaction_code", "direction"]).size().rename("lines").reset_index()
    return out


def profile_md(p: dict) -> str:
    parts = ["# Data profile", "", "Distributions of the generated data (evidence for realistic, varied data).", ""]
    for name, df in p.items():
        parts += [f"## {name.replace('_', ' ').capitalize()}", "", md_table(df), ""]
    return "\n".join(parts)
