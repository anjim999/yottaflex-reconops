"""Money helpers. All amounts are integers in minor units (cents, paise, yen)."""
from decimal import ROUND_HALF_EVEN, Decimal

from .config import CURRENCIES


def fee_minor(gross_minor: int, fee_rate_bps: int, fixed_fee_minor: int) -> int:
    """Processing fee on a capture: percentage (banker's rounding) + fixed fee.

    Refunds carry no fee and the original fee is not returned (documented fee policy).
    """
    gross_minor, fee_rate_bps, fixed_fee_minor = int(gross_minor), int(fee_rate_bps), int(fixed_fee_minor)
    pct = (Decimal(gross_minor) * fee_rate_bps / Decimal(10_000)).quantize(Decimal(1), ROUND_HALF_EVEN)
    return int(pct) + fixed_fee_minor


def to_major(amount_minor: int, currency: str) -> float:
    return amount_minor / 10 ** CURRENCIES[currency].exponent


def fmt(amount_minor: int, currency: str) -> str:
    exp = CURRENCIES[currency].exponent
    return f"{amount_minor / 10 ** exp:,.{exp}f} {currency}"
