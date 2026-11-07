import pandas as pd

from recon.engine.run import reconcile
from recon.metrics import decision_accuracy, detection_scores


def test_every_injected_anomaly_detected_without_false_positives(out, gt):
    scores = detection_scores(out["exceptions"], gt).set_index("exception_type")
    assert scores.loc["ALL (micro)", "recall"] == 1.0
    assert scores.loc["ALL (micro)", "precision"] == 1.0


def test_normal_tricky_cases_get_expected_decision(out, gt):
    d = decision_accuracy(out, gt)
    assert (d.accuracy == 1.0).all(), d


def test_matched_amounts_within_tolerance(out, run):
    tol = run["run_config"]["rules"]["amount_tolerance_minor"]
    m = out["reconciliation_matches"]
    assert (m[m.status == "MATCHED"].difference_minor.abs() <= tol).all()


def test_every_unmatched_item_is_an_exception(out):
    s = out["item_status"]
    assert set(s.recon_status) <= {"MATCHED", "PARTIAL", "EXCEPTION", "IN_TRANSIT", "OUT_OF_PERIOD", "OUT_OF_SCOPE"}
    m, items, x = out["reconciliation_matches"], out["match_items"], out["exceptions"]
    partial_batches = items[items.match_id.isin(m[m.status == "PARTIAL"].match_id) & (items.side == "LEFT")].entity_id
    assert partial_batches.isin(x.entity_id).all()


def test_duplicate_events_are_idempotent(run, out):
    t = dict(run["tables"])
    d = t["webhook_deliveries"]
    t["webhook_deliveries"] = pd.concat([d, d.assign(delivery_id=d.delivery_id.str.replace("DLV", "DLX"))])
    replay = reconcile(t, run["run_config"])
    assert replay["canonical_events"].event_id.equals(out["canonical_events"].event_id)
    cols = ["match_level", "match_type", "status", "left_amount_minor", "right_amount_minor"]
    assert replay["reconciliation_matches"][cols].equals(out["reconciliation_matches"][cols])


def test_engine_deterministic(run, out):
    again = reconcile(run["tables"], run["run_config"])
    for k in out:
        pd.testing.assert_frame_equal(out[k], again[k])


def test_fee_and_refund_treatment_consistent(out):
    assert not (out["exceptions"].exception_type == "FEE_RULE_VIOLATION").any()


def test_fee_difference_is_partial_not_matched(out, gt):
    fee_batches = set(gt[gt.issue_type == "BANK_AMOUNT_DIFFERS_BY_FEE"].entity_id)
    items = out["match_items"].merge(out["reconciliation_matches"], on="match_id")
    st = items[items.entity_id.isin(fee_batches)].status
    assert (st == "PARTIAL").all() and len(st) == len(fee_batches)


def test_exception_history_append_only_and_status_derived(out):
    h = out["exception_status_history"].sort_values("history_id")
    last = h.groupby("exception_id").to_status.last()
    x = out["exceptions"].set_index("exception_id")
    assert (x.status == last).all()
    assert h.groupby("exception_id").head(1).to_status.eq("OPEN").all()
    resolved = set(x[x.status == "RESOLVED"].index)
    assert resolved == set(out["resolutions"].exception_id)


def test_traceability_every_exception_points_at_a_real_record(tables, out):
    x = out["exceptions"]
    ids = set().union(*[set(df.iloc[:, 0]) for df in tables.values()])
    assert x.entity_id.isin(ids).all()
