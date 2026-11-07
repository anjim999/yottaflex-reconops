"""Data-quality validation: keys, FKs, enums, dates, arithmetic, lifecycle, duplicates, acceptance rules.

Deliberately injected anomalies are excluded via ground truth so the report shows
"0 unlabelled violations" while still counting the labelled ones.
"""
import re

import pandas as pd

from .generate.status import ORDER_TRANSITIONS
from .fees import FeeBook
from .schema import TABLES

ENTITY_TABLE = {"PAYMENT_ORDER": ("payment_orders", "payment_id"), "PROCESSOR_EVENT": ("processor_events", "event_id"),
                "WEBHOOK_DELIVERY": ("webhook_deliveries", "delivery_id"), "SETTLEMENT_BATCH": ("settlement_batches", "batch_id"),
                "SETTLEMENT_LINE": ("settlement_lines", "settlement_line_id"), "BANK_LINE": ("bank_statement_lines", "bank_line_id")}


class Report:
    def __init__(self):
        self.rows = []

    def add(self, category, check, table, failures, checked, labelled=0, note=""):
        self.rows.append({"category": category, "check": check, "table": table, "checked": int(checked),
                          "failures": int(failures), "labelled_anomalies": int(labelled),
                          "status": "PASS" if failures == 0 else "FAIL", "note": note})


def validate(t: dict, gt: pd.DataFrame, run_config: dict) -> pd.DataFrame:
    r = Report()
    gt_ids = lambda issue: set(gt.loc[gt.issue_type == issue, "entity_id"])
    _schema_checks(t, r)
    _fk_checks(t, r)

    o, a, e = t["payment_orders"], t["payment_attempts"], t["processor_events"]
    oc = o.set_index("payment_id").created_at
    r.add("date_ordering", "attempt.created_at >= order.created_at", "payment_attempts",
          (a.created_at < a.payment_id.map(oc)).sum(), len(a))
    ac = a.set_index("attempt_id").created_at
    rbc = gt.loc[gt.issue_type == "REFUND_BEFORE_CAPTURE", "detail"].str.replace("refund event ", "")
    bad = e[e.occurred_at < e.attempt_id.map(ac)]
    r.add("date_ordering", "event.occurred_at >= attempt.created_at", "processor_events",
          (~bad.event_id.isin(set(rbc))).sum(), len(e), bad.event_id.isin(set(rbc)).sum())
    cap = e[e.event_type == "payment.captured"].set_index("payment_id").occurred_at
    ref = e[e.event_type == "payment.refunded"]
    bad = ref[ref.occurred_at < ref.payment_id.map(cap)]
    lab = bad.payment_id.isin(gt_ids("REFUND_BEFORE_CAPTURE"))
    r.add("date_ordering", "refund.occurred_at >= capture.occurred_at", "processor_events", (~lab).sum(), len(ref), lab.sum())
    d = t["webhook_deliveries"]
    r.add("date_ordering", "delivery.received_at >= occurred_at", "webhook_deliveries", (d.received_at < d.occurred_at).sum(), len(d))
    b = t["bank_statement_lines"]
    r.add("date_ordering", "booking_date >= value_date", "bank_statement_lines", (b.booking_date < b.value_date).sum(), len(b))
    m = t["merchants"]
    r.add("date_ordering", "effective_to null or >= effective_from", "merchants",
          (m.effective_to.notna() & (m.effective_to < m.effective_from)).sum(), len(m))

    _arithmetic(t, gt, r)
    _lifecycle(t, r)

    dup_d = d[d.duplicated("event_id", keep="first")]
    lab = dup_d.delivery_id.isin(gt_ids("DUPLICATE_PROCESSOR_EVENT"))
    r.add("duplicates", "duplicate webhook deliveries are labelled", "webhook_deliveries", (~lab).sum(), len(d), lab.sum())
    sl = t["settlement_lines"].sort_values("settlement_line_id")
    dup_l = sl[sl.duplicated("event_id", keep="first")]
    lab = dup_l.settlement_line_id.isin(gt_ids("DUPLICATE_SETTLEMENT_LINE"))
    r.add("duplicates", "duplicate settlement lines are labelled", "settlement_lines", (~lab).sum(), len(sl), lab.sum())
    acc_ccy = b.account_id.str[4:7]
    bad = b[acc_ccy != b.currency]
    lab = bad.bank_line_id.isin(set(gt.loc[gt.issue_type == "CURRENCY_MISMATCH", "detail"].str[:16]))
    r.add("consistency", "bank line currency = account currency", "bank_statement_lines", (~lab).sum(), len(b), lab.sum())

    tg = run_config["targets"]
    for table, key in [("merchants", "merchants"), ("payment_orders", "orders"), ("payment_attempts", "attempts"),
                       ("settlement_batches", "batches"), ("bank_statement_lines", "bank_lines")]:
        r.add("volume", f"row count = target {tg[key]}", table, int(len(t[table]) != tg[key]), 1, note=f"actual {len(t[table])}")

    if "exceptions" in t:
        _acceptance(t, run_config, r)
    return pd.DataFrame(r.rows)


def _schema_checks(t, r):
    for name, (_, pk, fields) in TABLES.items():
        if name not in t:
            continue
        df = t[name]
        keys = pk.split(",")
        r.add("primary_key", f"unique, non-null ({pk})", name, df.duplicated(keys).sum() + df[keys].isna().any(axis=1).sum(), len(df))
        for f in fields:
            col = df[f.name]
            if f.required:
                r.add("required", f"{f.name} not null", name, col.isna().sum(), len(df))
            if f.allowed:
                allowed = {str(v) for v in f.allowed}
                r.add("enum", f"{f.name} in allowed values", name, (~col.dropna().astype(str).isin(allowed)).sum(), len(df))
            if f.pattern:
                rx = re.compile(f.pattern)
                r.add("id_format", f"{f.name} matches {f.pattern}", name, (~col.dropna().map(lambda v: bool(rx.match(v)))).sum(), len(df))
            if f.unique and f.name != pk:
                r.add("unique", f"{f.name} unique", name, col.dropna().duplicated().sum(), len(df))


def _fk_checks(t, r):
    for name, (_, _, fields) in TABLES.items():
        if name not in t:
            continue
        for f in fields:
            if f.fk:
                pt, pc = f.fk.split(".")
                if pt in t:
                    col = t[name][f.name].dropna()
                    r.add("foreign_key", f"{f.name} -> {f.fk}", name, (~col.isin(set(t[pt][pc]))).sum(), len(col))
    for name in ("exceptions", "match_items", "item_status"):
        if name in t:
            df = t[name].rename(columns={"item_type": "entity_type", "item_id": "entity_id"})
            miss = sum((~g.entity_id.isin(set(t[ENTITY_TABLE[et][0]][ENTITY_TABLE[et][1]]))).sum()
                       for et, g in df.groupby("entity_type"))
            r.add("foreign_key", "polymorphic entity_id exists", name, miss, len(df))


def _arithmetic(t, gt, r):
    sl, sb, m, o = t["settlement_lines"], t["settlement_batches"], t["merchants"], t["payment_orders"]
    cap = sl.line_type == "CAPTURE"
    r.add("arithmetic", "line net = gross - fee (capture) / -gross (refund)", "settlement_lines",
          ((cap & (sl.net_minor != sl.gross_minor - sl.fee_minor)) | (~cap & (sl.net_minor != -sl.gross_minor))).sum(), len(sl))
    mer = m.set_index("merchant_id")
    fs = t["merchant_fee_schedules"].copy()
    fs["effective_from"] = pd.to_datetime(fs.effective_from).dt.date
    book = FeeBook(fs)
    cap_at = t["processor_events"].set_index("event_id").occurred_at.str[:10].map(pd.Timestamp.fromisoformat)
    exp = [book.fee(mid, cap_at[eid].date(), int(g)) if lt == "CAPTURE" else 0
           for g, mid, lt, eid in zip(sl.gross_minor, sl.merchant_id, sl.line_type, sl.event_id)]
    r.add("arithmetic", "line fee = fee schedule in force on capture date (refund fee 0)", "settlement_lines",
          (sl.fee_minor != pd.Series(exp, index=sl.index)).sum(), len(sl))
    _fee_schedule_checks(t["merchant_fee_schedules"], m, r)
    g = sl.groupby("batch_id")
    j = sb.set_index("batch_id")
    bad = ((j.line_count != g.size()) | (j.fee_minor != g.fee_minor.sum()) | (j.net_minor != g.net_minor.sum())
           | (j.net_minor != j.gross_capture_minor - j.gross_refund_minor - j.fee_minor))
    r.add("arithmetic", "batch totals = sum of lines; net = cap - ref - fee", "settlement_batches", bad.sum(), len(sb))
    e = t["processor_events"]
    capd = e[e.event_type == "payment.captured"].groupby("payment_id").amount_minor.sum()
    refd = e[e.event_type == "payment.refunded"].groupby("payment_id").amount_minor.sum()
    oi = o.set_index("payment_id")
    bad = (oi.captured_amount_minor != capd.reindex(oi.index).fillna(0)) | (oi.refunded_amount_minor != refd.reindex(oi.index).fillna(0))
    r.add("arithmetic", "order captured/refunded = sum of events", "payment_orders", bad.sum(), len(o))
    r.add("arithmetic", "refunded <= captured", "payment_orders", (oi.refunded_amount_minor > oi.captured_amount_minor).sum(), len(o))
    r.add("consistency", "order currency = merchant currency", "payment_orders",
          (o.currency != o.merchant_id.map(mer.settlement_currency)).sum(), len(o))


def _lifecycle(t, r):
    h = t["order_status_history"].sort_values(["payment_id", "history_id"])
    prev = h.groupby("payment_id").to_status.shift()
    bad = [to not in ORDER_TRANSITIONS[None if pd.isna(fr) else fr] for fr, to in zip(prev, h.to_status)]
    r.add("lifecycle", "order transitions allowed", "order_status_history", sum(bad), len(h))
    r.add("lifecycle", "history from_status = previous to_status", "order_status_history",
          (h.from_status.fillna("") != prev.fillna("")).sum(), len(h))
    last = h.groupby("payment_id").to_status.last()
    o = t["payment_orders"].set_index("payment_id")
    r.add("lifecycle", "order.status = last history row", "payment_orders", (o.status != last.reindex(o.index)).sum(), len(o))
    a = t["payment_attempts"]
    r.add("lifecycle", "failed attempt has failure_code", "payment_attempts", ((a.status == "FAILED") & a.failure_code.isna()).sum(), len(a))


def _acceptance(t, run_config, r):
    tol = run_config["rules"]["amount_tolerance_minor"]
    m = t["reconciliation_matches"]
    ok = m[m.status == "MATCHED"]
    r.add("acceptance", f"matched amounts within tolerance ({tol} minor)", "reconciliation_matches",
          (ok.difference_minor.abs() > tol).sum(), len(ok))
    s = t["item_status"]
    x = t["exceptions"]
    unexplained = ~s.recon_status.isin(["MATCHED", "PARTIAL", "EXCEPTION", "IN_TRANSIT", "OUT_OF_PERIOD", "OUT_OF_SCOPE"])
    r.add("acceptance", "every item matched, explained or an exception", "item_status", unexplained.sum(), len(s))
    items = t["match_items"]
    partial = items[items.match_id.isin(set(m.loc[m.status == "PARTIAL", "match_id"])) & (items.side == "LEFT")]
    r.add("acceptance", "every partial match has an exception", "reconciliation_matches",
          (~partial.entity_id.isin(set(x.entity_id) | set(x.related_ids.fillna("").str.split("|").explode()))).sum(), len(partial))
    sl_ids = set(t["settlement_lines"].settlement_line_id)
    matched_lines = set(items.loc[items.entity_type == "SETTLEMENT_LINE", "entity_id"])
    exc_lines = set(x.loc[x.entity_type == "SETTLEMENT_LINE", "entity_id"])
    r.add("acceptance", "every settlement line is matched or an exception", "settlement_lines",
          len(sl_ids - matched_lines - exc_lines), len(sl_ids))
    ce, pe = t["canonical_events"], t["processor_events"]
    r.add("acceptance", "dedup is idempotent: canonical events = registry", "canonical_events",
          len(set(ce.event_id) ^ set(pe.event_id)) + ce.event_id.duplicated().sum(), len(pe))
    r.add("acceptance", "fee/refund treatment consistent (no fee-rule exceptions)", "exceptions",
          (x.exception_type == "FEE_RULE_VIOLATION").sum(), len(x))
    h = t["exception_status_history"].sort_values("history_id")
    last = h.groupby("exception_id").to_status.last()
    r.add("lifecycle", "exception.status = latest history row", "exceptions", (x.set_index("exception_id").status != last).sum(), len(x))
    res = t["resolutions"]
    resolved = set(x.loc[x.status == "RESOLVED", "exception_id"])
    r.add("lifecycle", "resolved exceptions have exactly one resolution", "resolutions",
          len(resolved ^ set(res.exception_id)), len(res))


def _fee_schedule_checks(fs, merchants, r):
    """Effective dating: one open version per merchant, contiguous with no gaps or overlaps."""
    fs = fs.sort_values(["merchant_id", "version"])
    nxt = fs.groupby("merchant_id").effective_from.shift(-1)
    gap = nxt.notna() & (pd.to_datetime(fs.effective_to) + pd.Timedelta(days=1) != pd.to_datetime(nxt))
    r.add("effective_dating", "fee versions contiguous (to + 1 day = next from)", "merchant_fee_schedules", gap.sum(), len(fs))
    r.add("effective_dating", "effective_to null or >= effective_from", "merchant_fee_schedules",
          (fs.effective_to.notna() & (fs.effective_to < fs.effective_from)).sum(), len(fs))
    open_n = fs[fs.effective_to.isna()].groupby("merchant_id").size().reindex(merchants.merchant_id).fillna(0)
    r.add("effective_dating", "exactly one current fee version per merchant", "merchant_fee_schedules", (open_n != 1).sum(), len(merchants))
    v1 = fs[fs.version == 1].set_index("merchant_id").effective_from
    r.add("effective_dating", "v1 starts at merchant onboarding", "merchant_fee_schedules",
          (merchants.set_index("merchant_id").onboarded_on != v1.reindex(merchants.merchant_id)).sum(), len(merchants))
