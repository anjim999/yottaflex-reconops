import re

import pandas as pd

from recon.config import SCALES
from recon.generate.pipeline import generate
from recon.ids import PATTERNS, attempt_id, batch_id, line_id, payment_id


def test_id_formats_match_brief():
    assert payment_id(1) == "PAY-2026-00000001"
    assert attempt_id(payment_id(1), 1) == "ATT-PAY-2026-00000001-01"
    assert batch_id(1) == "SET-2026-000001"
    assert line_id(batch_id(1), 1) == "STL-SET-2026-000001-001"


def test_volumes_hit_targets(tables):
    s = SCALES["starter"]
    assert len(tables["merchants"]) == s.merchants
    assert len(tables["payment_orders"]) == s.orders
    assert len(tables["payment_attempts"]) == s.attempts
    assert len(tables["settlement_batches"]) == s.batches
    assert len(tables["bank_statement_lines"]) == s.bank_lines


def test_ids_well_formed_and_unique(tables):
    for table, col, pat in [("payment_orders", "payment_id", "payment_id"), ("payment_attempts", "attempt_id", "attempt_id"),
                            ("settlement_batches", "batch_id", "batch_id"),
                            ("settlement_lines", "settlement_line_id", "settlement_line_id"),
                            ("bank_statement_lines", "bank_line_id", "bank_line_id")]:
        ids = tables[table][col]
        assert ids.is_unique
        assert ids.map(lambda v: bool(re.match(PATTERNS[pat], v))).all()


def test_foreign_keys(tables):
    t = tables
    assert t["payment_orders"].merchant_id.isin(t["merchants"].merchant_id).all()
    assert t["payment_attempts"].payment_id.isin(t["payment_orders"].payment_id).all()
    assert t["processor_events"].attempt_id.isin(t["payment_attempts"].attempt_id).all()
    assert t["settlement_lines"].batch_id.isin(t["settlement_batches"].batch_id).all()
    assert t["settlement_lines"].event_id.isin(t["processor_events"].event_id).all()
    assert t["webhook_deliveries"].event_id.isin(t["processor_events"].event_id).all()


def test_attempt_belongs_to_its_payment(tables):
    a = tables["payment_attempts"]
    assert (a.attempt_id.str[4:21] == a.payment_id).all()


def test_batch_totals_derived_from_lines(tables):
    lines, b = tables["settlement_lines"], tables["settlement_batches"].set_index("batch_id")
    g = lines.groupby("batch_id")
    assert (b.net_minor == g.net_minor.sum()).all()
    assert (b.net_minor == b.gross_capture_minor - b.gross_refund_minor - b.fee_minor).all()
    assert (lines[lines.line_type == "REFUND"].fee_minor == 0).all()


def test_required_baseline_variety(tables, gt):
    e = tables["processor_events"]
    refunds = e[e.event_type == "payment.refunded"].set_index("payment_id").amount_minor
    captured = e[e.event_type == "payment.captured"].set_index("payment_id").amount_minor
    assert (refunds < captured.reindex(refunds.index)).any(), "partial refunds present"
    assert (tables["settlement_lines"].fee_minor > 0).any(), "fees present"
    assert "JPY" in set(tables["payment_orders"].currency), "zero-decimal currency present"
    for issue in ["DELAYED_SETTLEMENT", "ROUNDING_DIFFERENCE", "SPLIT_PAYOUT", "MISSING_BANK_REFERENCE"]:
        assert (gt.issue_type == issue).any(), issue


def test_all_required_edge_cases_labelled(gt):
    required = {"DUPLICATE_SETTLEMENT_LINE", "BANK_AMOUNT_DIFFERS_BY_FEE", "REFUND_BEFORE_CAPTURE",
                "UNMATCHED_RECORD_DROPPED", "CURRENCY_MISMATCH", "DUPLICATE_PROCESSOR_EVENT"}
    assert required <= set(gt[gt.category == "ANOMALY"].issue_type)


def test_ground_truth_not_leaked_into_inputs(tables):
    for name, df in tables.items():
        cols = {c.lower() for c in df.columns}
        assert not cols & {"issue_type", "ground_truth", "is_anomaly", "expected_exception_type"}, name


def test_same_seed_is_reproducible(tables):
    again = generate("starter", 20261022)["tables"]
    for name, df in tables.items():
        pd.testing.assert_frame_equal(df, again[name])


def test_different_seed_changes_data(tables):
    other = generate("starter", 1)["tables"]
    assert not tables["payment_orders"].amount_minor.equals(other["payment_orders"].amount_minor)


def test_effective_dated_fees_applied_by_capture_date(tables):
    from datetime import date

    from recon.money import fee_minor

    fs = tables["merchant_fee_schedules"]
    repriced = fs[fs.version == 2]
    assert len(repriced) > 0, "some merchants are repriced mid-period"
    ev = tables["processor_events"].set_index("event_id").occurred_at
    lines = tables["settlement_lines"]
    checked = set()
    for r in repriced.itertuples():
        v1 = fs[(fs.merchant_id == r.merchant_id) & (fs.version == 1)].iloc[0]
        caps = lines[(lines.merchant_id == r.merchant_id) & (lines.line_type == "CAPTURE")]
        for ln in caps.itertuples():
            on = date.fromisoformat(ev[ln.event_id][:10])
            terms = r if on >= date.fromisoformat(r.effective_from) else v1
            assert ln.fee_minor == fee_minor(ln.gross_minor, terms.fee_rate_bps, terms.fixed_fee_minor)
            checked.add("v2" if terms is r else "v1")
    assert checked == {"v1", "v2"}, "both fee versions exercised"
