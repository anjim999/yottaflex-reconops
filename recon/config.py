"""Central configuration: seed, scale profiles and business-rule parameters.

Every tunable number lives here so the generator and the engine share one source of truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone

DEFAULT_SEED = 20261022
GENERATOR_VERSION = "1.0.0"
ID_YEAR = 2026
UTC = timezone.utc

START_DATE = date(2026, 1, 1)  # first day of the reconciliation period's order activity
WARMUP_DAYS = 3                # orders created before START_DATE so early batches have volume
PROCESSOR_CODE = "NOVAPAY"     # fictional processor
PROCESSOR_NAME = "NOVAPAY SETTLEMENTS LTD"


@dataclass(frozen=True)
class Currency:
    code: str
    exponent: int          # minor-unit exponent (JPY = 0)
    volume_share: float    # share of payment orders
    fx_per_usd: float      # only used to scale synthetic amounts realistically
    fixed_fee_minor: int   # per-capture fixed processing fee
    wire_fee_minor: int    # incoming-wire fee some banks deduct from payouts
    countries: tuple


CURRENCIES = {c.code: c for c in [
    Currency("USD", 2, 0.40, 1.00, 30, 1500, ("US",)),
    Currency("EUR", 2, 0.25, 0.92, 25, 1200, ("DE", "FR", "ES", "IT", "NL")),
    Currency("GBP", 2, 0.15, 0.79, 20, 1000, ("GB",)),
    Currency("INR", 2, 0.12, 83.0, 300, 50000, ("IN",)),
    Currency("JPY", 0, 0.08, 150.0, 30, 2000, ("JP",)),
]}
CURRENCY_CODES = tuple(CURRENCIES)


@dataclass(frozen=True)
class Scale:
    name: str
    merchants: int
    orders: int
    attempts: int
    batches: int      # one batch per currency per settlement day -> must be divisible by 5
    bank_lines: int

    @property
    def settlement_days(self) -> int:
        return self.batches // len(CURRENCIES)


SCALES = {
    "starter": Scale("starter", 200, 5_000, 5_500, 100, 500),
    "full": Scale("full", 2_000, 50_000, 55_000, 1_000, 5_000),
}


@dataclass(frozen=True)
class Rules:
    """Matching rules used by the reconciliation engine."""
    amount_tolerance_minor: int = 1   # absolute tolerance in minor units (currency rounding)
    date_window_days: int = 3         # bank value date must fall in [settlement_date, +N days]
    settlement_grace_days: int = 4    # how late a capture may settle before it is "missing"


RULES = Rules()

# Baseline (normal-behaviour) distribution parameters.
MIX = {
    "final_fail_rate": 0.04,          # orders whose last attempt fails
    "void_rate": 0.02,                # authorized then voided
    "delayed_capture_share": 0.15,    # manual capture 1-48h after auth
    "refund_rate": 0.10,
    "partial_refund_share": 0.70,
    "delayed_settlement_rate": 0.04,  # extra 1-3 days before settlement
    "max_extra_settlement_delay": 3,
    "split_payout_rate": 0.08,        # one batch paid as two bank credits
    "rounding_rate": 0.03,            # bank amount off by 1 minor unit
    "missing_reference_rate": 0.03,   # bank truncated the reference -> fuzzy match
    "bank_lag_probs": (0.70, 0.25, 0.05),  # value date = settlement date + 0/1/2 days
    "duplicate_webhook_rate": 0.015,  # same processor event delivered twice
    "triple_webhook_share": 0.10,     # of duplicates, delivered three times
}

# Labelled anomaly volume per 1,000 settlement batches (scaled, minimum 3).
ANOMALY_BASE = {
    "DUPLICATE_SETTLEMENT_LINE": 30,
    "BANK_AMOUNT_DIFFERS_BY_FEE": 20,
    "REFUND_BEFORE_CAPTURE": 30,
    "UNMATCHED_RECORD_DROPPED_LINE": 30,
    "UNMATCHED_RECORD_ORPHAN_BANK": 10,
    "CURRENCY_MISMATCH": 15,
}


def anomaly_counts(scale: Scale) -> dict[str, int]:
    return {k: max(3, round(v * scale.batches / 1000)) for k, v in ANOMALY_BASE.items()}


@dataclass(frozen=True)
class Period:
    order_start: date
    settlement_start: date
    settlement_end: date
    statement_end: date
    run_at: datetime

    def to_dict(self) -> dict:
        return {k: v.isoformat() for k, v in asdict(self).items()}

    @staticmethod
    def from_dict(d: dict) -> "Period":
        return Period(
            date.fromisoformat(d["order_start"]), date.fromisoformat(d["settlement_start"]),
            date.fromisoformat(d["settlement_end"]), date.fromisoformat(d["statement_end"]),
            datetime.fromisoformat(d["run_at"]),
        )


def period_for(scale: Scale) -> Period:
    s_start = START_DATE + timedelta(days=1)
    s_end = START_DATE + timedelta(days=scale.settlement_days)
    st_end = s_end + timedelta(days=2)
    run_at = datetime.combine(st_end + timedelta(days=1), time(6, 0), tzinfo=UTC)
    return Period(START_DATE - timedelta(days=WARMUP_DAYS), s_start, s_end, st_end, run_at)


def iso_ts(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
