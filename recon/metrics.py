"""Evaluation: engine decisions vs ground truth + operational reconciliation KPIs."""
import pandas as pd

from .money import to_major


def detection_scores(exceptions: pd.DataFrame, gt: pd.DataFrame) -> pd.DataFrame:
    """Precision / recall / F1 per exception type, keyed on (exception_type, entity_id)."""
    expected = gt[gt.expected_exception_type.notna()]
    exp_keys = set(zip(expected.expected_exception_type, expected.entity_id))
    got_keys = set(zip(exceptions.exception_type, exceptions.entity_id))
    rows = []
    for etype in sorted(set(expected.expected_exception_type) | set(exceptions.exception_type)):
        e = {k for k in exp_keys if k[0] == etype}
        g = {k for k in got_keys if k[0] == etype}
        tp, fp, fn = len(e & g), len(g - e), len(e - g)
        p = tp / (tp + fp) if tp + fp else 1.0
        rc = tp / (tp + fn) if tp + fn else 1.0
        rows.append({"exception_type": etype, "expected": len(e), "detected": len(g), "true_positive": tp,
                     "false_positive": fp, "false_negative": fn, "precision": round(p, 4), "recall": round(rc, 4),
                     "f1": round(2 * p * rc / (p + rc), 4) if p + rc else 0.0})
    df = pd.DataFrame(rows)
    tp, fp, fn = df.true_positive.sum(), df.false_positive.sum(), df.false_negative.sum()
    p, rc = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    total = {"exception_type": "ALL (micro)", "expected": df.expected.sum(), "detected": df.detected.sum(),
             "true_positive": tp, "false_positive": fp, "false_negative": fn, "precision": round(p, 4),
             "recall": round(rc, 4), "f1": round(2 * p * rc / (p + rc), 4) if p + rc else 0.0}
    return pd.concat([df, pd.DataFrame([total])], ignore_index=True)


def decision_accuracy(out: dict, gt: pd.DataFrame) -> pd.DataFrame:
    """Normal-but-tricky labelled cases: did the engine make the expected (non-exception) decision?"""
    m, items, st = out["reconciliation_matches"], out["match_items"], out["item_status"]
    batch_match = items[items.entity_type == "SETTLEMENT_BATCH"].merge(m, on="match_id").set_index("entity_id")
    status = st.set_index(["item_type", "item_id"]).recon_status
    expect_type = {"MATCHED_SPLIT": "SPLIT", "MATCHED_WITHIN_TOLERANCE": "WITHIN_TOLERANCE", "MATCHED_FUZZY": "FUZZY"}
    rows = []
    for issue, g in gt[gt.category == "NORMAL"].groupby("issue_type"):
        ok = 0
        for r in g.itertuples():
            if r.entity_type == "SETTLEMENT_BATCH":
                ok += r.entity_id in batch_match.index and batch_match.loc[r.entity_id, "match_type"] == expect_type[r.expected_decision] \
                    and batch_match.loc[r.entity_id, "status"] == "MATCHED"
            else:
                ok += status.get(("PROCESSOR_EVENT", r.entity_id)) == "MATCHED"
        rows.append({"issue_type": issue, "expected_decision": g.expected_decision.iloc[0], "cases": len(g),
                     "correct": int(ok), "accuracy": round(ok / len(g), 4)})
    return pd.DataFrame(rows)


def kpis(t: dict, out: dict) -> dict:
    st, m, x, res = out["item_status"], out["reconciliation_matches"], out["exceptions"], out["resolutions"]
    by = lambda typ: st[st.item_type == typ].recon_status.value_counts().to_dict()
    in_scope = lambda typ: st[(st.item_type == typ) & ~st.recon_status.isin(["OUT_OF_SCOPE", "OUT_OF_PERIOD", "IN_TRANSIT"])]
    rate = lambda typ: round((in_scope(typ).recon_status == "MATCHED").mean(), 4)
    bm = m[(m.match_level == "BATCH_TO_BANK") & (m.status == "MATCHED")]
    b = t["settlement_batches"]
    usd = lambda df, col: sum(to_major(int(v), c) / {"USD": 1, "EUR": .92, "GBP": .79, "INR": 83, "JPY": 150}[c]
                              for v, c in zip(df[col], df.currency) if pd.notna(v) and pd.notna(c))
    open_x = x[x.status != "RESOLVED"]
    return {
        "event_settlement_match_rate": rate("PROCESSOR_EVENT"),
        "settlement_line_match_rate": rate("SETTLEMENT_LINE"),
        "batch_bank_match_rate": rate("SETTLEMENT_BATCH"),
        "processor_bank_line_match_rate": rate("BANK_LINE"),
        "status_breakdown": {k: by(k) for k in ["PROCESSOR_EVENT", "SETTLEMENT_LINE", "SETTLEMENT_BATCH", "BANK_LINE"]},
        "settled_net_usd_equiv": round(usd(b, "net_minor"), 2),
        "matched_net_usd_equiv": round(usd(bm, "left_amount_minor"), 2),
        "amount_match_rate": round(usd(bm, "left_amount_minor") / max(usd(b, "net_minor"), 1), 4),
        "exceptions_total": len(x),
        "exceptions_by_type": x.exception_type.value_counts().to_dict(),
        "exceptions_by_severity": x.severity.value_counts().to_dict(),
        "exceptions_by_status": x.status.value_counts().to_dict(),
        "resolution_rate": round(len(res) / max(len(x), 1), 4),
        "open_exception_amount_usd_equiv": round(usd(open_x, "amount_minor"), 2),
    }
