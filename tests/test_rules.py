"""Focused unit tests on single rules with tiny hand-built inputs."""
from datetime import date

import pandas as pd

from recon.config import PROCESSOR_NAME, Period, Rules
from recon.engine.ingest import ingest_deliveries
from recon.engine.ledger import Ledger
from recon.engine.match_bank import match_batches_to_bank
from recon.money import fee_minor

RULES = Rules()
PERIOD = Period(date(2025, 12, 29), date(2026, 1, 2), date(2026, 1, 20), date(2026, 1, 22),
                pd.Timestamp("2026-01-23T06:00:00Z").to_pydatetime())


def test_fee_uses_bankers_rounding():
    assert fee_minor(1000, 250, 30) == 25 + 30
    assert fee_minor(50, 150, 0) == 1  # 0.75 -> 1
    assert fee_minor(30, 150, 0) == 0  # 0.45 -> 0


def _batch(net, ccy="USD", fee=100, bid="SET-2026-000001"):
    return pd.DataFrame([{"batch_id": bid, "currency": ccy, "settlement_date": date(2026, 1, 5), "net_minor": net,
                          "fee_minor": fee}])


def _bank(amount, ccy="USD", ref="NOVAPAY PAYOUT SET-2026-000001", vdate=date(2026, 1, 5)):
    return pd.DataFrame([{"bank_line_id": "BANK-2026-000001", "direction": "CREDIT", "amount_minor": amount,
                          "currency": ccy, "reference": ref, "counterparty": PROCESSOR_NAME, "value_date": vdate}])


def _run(batch, bank):
    led = Ledger("2026-01-23T06:00:00Z")
    match_batches_to_bank(batch, bank, RULES, PERIOD, led)
    return led


def test_exact_and_tolerance_match():
    assert _run(_batch(10_000), _bank(10_000)).matches[0]["match_type"] == "EXACT"
    led = _run(_batch(10_000), _bank(10_001))
    assert led.matches[0]["match_type"] == "WITHIN_TOLERANCE" and not led.exceptions


def test_beyond_tolerance_is_exception():
    led = _run(_batch(10_000), _bank(10_002))
    assert led.exceptions[0]["exception_type"] == "BANK_AMOUNT_MISMATCH"


def test_fee_difference_detected():
    led = _run(_batch(10_000, fee=250), _bank(10_250))
    assert led.exceptions[0]["exception_type"] == "FEE_DIFFERENCE"


def test_currency_mismatch_never_auto_matched():
    led = _run(_batch(10_000), _bank(10_000, ccy="EUR"))
    assert not led.matches and led.exceptions[0]["exception_type"] == "CURRENCY_MISMATCH"


def test_date_window_enforced():
    led = _run(_batch(10_000), _bank(10_000, vdate=date(2026, 1, 9)))
    assert led.exceptions[0]["exception_type"] == "PAYOUT_OUTSIDE_DATE_WINDOW"


def test_fuzzy_match_without_reference():
    led = _run(_batch(10_000), _bank(10_000, ref=None))
    assert led.matches[0]["match_type"] == "FUZZY"


def test_unreferenced_unknown_credit_is_exception():
    led = _run(_batch(10_000), _bank(55_555, ref=None))
    types = {x["exception_type"] for x in led.exceptions}
    assert {"UNMATCHED_BANK_LINE", "UNMATCHED_SETTLEMENT_BATCH"} <= types


def test_webhook_dedup_keeps_first_and_flags_conflicts():
    base = {"event_id": "EVT-2026-00000001", "payment_id": "P", "attempt_id": "A", "event_type": "payment.captured",
            "amount_minor": 100, "currency": "USD", "occurred_at": pd.Timestamp("2026-01-01", tz="UTC")}
    d = pd.DataFrame([{**base, "delivery_id": "DLV-2", "received_at": pd.Timestamp("2026-01-01 00:01", tz="UTC")},
                      {**base, "delivery_id": "DLV-1", "received_at": pd.Timestamp("2026-01-01 00:00", tz="UTC")},
                      {**base, "amount_minor": 999, "delivery_id": "DLV-3", "received_at": pd.Timestamp("2026-01-01 00:02", tz="UTC")}])
    led = Ledger("t")
    canon = ingest_deliveries(d, led)
    assert len(canon) == 1 and canon.first_delivery_id[0] == "DLV-1"
    assert [x["exception_type"] for x in led.exceptions] == ["DUPLICATE_WEBHOOK", "WEBHOOK_PAYLOAD_CONFLICT"]
