"""Deterministic, immutable, zero-padded identifiers.

Formats required by the brief: PAY-2026-00000001, ATT-<payment-id>-01, SET-2026-000001,
STL-<batch-id>-001, BANK-2026-000001, REC-2026-000001. The rest follow the same style.
"""
from .config import ID_YEAR

Y = ID_YEAR


def merchant_id(n: int) -> str: return f"MER-{n:06d}"
def customer_ref(n: int) -> str: return f"CUS-{n:07d}"
def fee_schedule_id(n: int) -> str: return f"FEE-{n:06d}"
def payment_id(n: int) -> str: return f"PAY-{Y}-{n:08d}"
def attempt_id(pid: str, n: int) -> str: return f"ATT-{pid}-{n:02d}"
def event_id(n: int) -> str: return f"EVT-{Y}-{n:08d}"
def delivery_id(n: int) -> str: return f"DLV-{Y}-{n:08d}"
def batch_id(n: int) -> str: return f"SET-{Y}-{n:06d}"
def bank_line_id(n: int) -> str: return f"BANK-{Y}-{n:06d}"
def match_id(n: int) -> str: return f"REC-{Y}-{n:06d}"
def exception_id(n: int) -> str: return f"EXC-{Y}-{n:06d}"
def resolution_id(n: int) -> str: return f"RES-{Y}-{n:06d}"
def order_history_id(n: int) -> str: return f"OSH-{Y}-{n:08d}"
def exception_history_id(n: int) -> str: return f"EXH-{Y}-{n:06d}"
def gt_id(n: int) -> str: return f"GT-{n:06d}"


def line_id(bid: str, n: int) -> str:
    if n > 999:
        raise ValueError(f"batch {bid} exceeds 999 settlement lines")
    return f"STL-{bid}-{n:03d}"


PATTERNS = {
    "merchant_id": r"^MER-\d{6}$",
    "customer_ref": r"^CUS-\d{7}$",
    "fee_schedule_id": r"^FEE-\d{6}$",
    "payment_id": rf"^PAY-{Y}-\d{{8}}$",
    "attempt_id": rf"^ATT-PAY-{Y}-\d{{8}}-\d{{2}}$",
    "event_id": rf"^EVT-{Y}-\d{{8}}$",
    "delivery_id": rf"^DLV-{Y}-\d{{8}}$",
    "batch_id": rf"^SET-{Y}-\d{{6}}$",
    "settlement_line_id": rf"^STL-SET-{Y}-\d{{6}}-\d{{3}}$",
    "bank_line_id": rf"^BANK-{Y}-\d{{6}}$",
    "match_id": rf"^REC-{Y}-\d{{6}}$",
    "exception_id": rf"^EXC-{Y}-\d{{6}}$",
    "resolution_id": rf"^RES-{Y}-\d{{6}}$",
    "order_history_id": rf"^OSH-{Y}-\d{{8}}$",
    "exception_history_id": rf"^EXH-{Y}-\d{{6}}$",
    "gt_id": r"^GT-\d{6}$",
}
