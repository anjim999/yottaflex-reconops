"""Single source of truth for every table: drives the data dictionary, SQL DDL and validation."""
from dataclasses import dataclass

from .config import CURRENCY_CODES
from .engine.catalog import EXCEPTIONS
from .ids import PATTERNS


@dataclass(frozen=True)
class F:
    name: str
    type: str                      # text | int | date | ts
    required: bool = True
    allowed: tuple = ()
    unit: str = ""
    unique: bool = False
    pattern: str = ""
    fk: str = ""                   # "table.column"
    rule: str = ""


CCY = tuple(CURRENCY_CODES)
ROLES = ("SYSTEM", "OPS_ANALYST", "RISK_REVIEWER")
ORDER_STATUS = ("CREATED", "AUTHORIZED", "CAPTURED", "PARTIALLY_REFUNDED", "REFUNDED", "FAILED", "VOIDED")
EVENT_TYPES = ("payment.authorized", "payment.captured", "payment.refunded", "payment.failed", "payment.voided")
ENTITY_TYPES = ("PAYMENT_ORDER", "PROCESSOR_EVENT", "WEBHOOK_DELIVERY", "SETTLEMENT_BATCH", "SETTLEMENT_LINE", "BANK_LINE")
MINOR = "minor currency units"

TABLES = {
    "merchants": ("Merchant master data (effective-dated fee terms).", "merchant_id", [
        F("merchant_id", "text", unique=True, pattern=PATTERNS["merchant_id"]),
        F("legal_name", "text"),
        F("country", "text", allowed=("US", "DE", "FR", "ES", "IT", "NL", "GB", "IN", "JP")),
        F("settlement_currency", "text", allowed=CCY),
        F("mcc", "text", rule="ISO 18245 merchant category code"),
        F("risk_tier", "text", allowed=("LOW", "MEDIUM", "HIGH")),
        F("settlement_delay_days", "int", unit="days", allowed=(1, 2, 3)),
        F("status", "text", allowed=("ACTIVE", "SUSPENDED")),
        F("onboarded_on", "date"),
        F("effective_from", "date", rule="merchant record valid from"),
        F("effective_to", "date", required=False, rule="null = current; >= effective_from"),
    ]),
    "merchant_fee_schedules": ("Effective-dated fee terms (SCD type 2). Fee applied = version in force on the capture date.", "fee_schedule_id", [
        F("fee_schedule_id", "text", unique=True, pattern=PATTERNS["fee_schedule_id"]),
        F("merchant_id", "text", fk="merchants.merchant_id"),
        F("version", "int", rule="1..n per merchant, contiguous"),
        F("fee_rate_bps", "int", unit="basis points", rule="100-400"),
        F("fixed_fee_minor", "int", unit=MINOR, rule=">= 0"),
        F("effective_from", "date", rule="v1 = onboarding date; v(n+1) = v(n).effective_to + 1 day"),
        F("effective_to", "date", required=False, rule="null = current version; no gaps or overlaps"),
    ]),
    "payment_orders": ("Customer payment order; status derived from events.", "payment_id", [
        F("payment_id", "text", unique=True, pattern=PATTERNS["payment_id"]),
        F("merchant_id", "text", fk="merchants.merchant_id"),
        F("customer_ref", "text", pattern=PATTERNS["customer_ref"], rule="pseudonymous synthetic customer"),
        F("amount_minor", "int", unit=MINOR, rule="> 0"),
        F("currency", "text", allowed=CCY, rule="= merchant settlement_currency"),
        F("payment_method", "text", allowed=("CARD", "WALLET", "BANK_TRANSFER")),
        F("created_at", "ts"),
        F("status", "text", allowed=ORDER_STATUS, rule="derived: last order_status_history row"),
        F("captured_amount_minor", "int", unit=MINOR, rule="derived: sum of capture events"),
        F("refunded_amount_minor", "int", unit=MINOR, rule="derived: sum of refunds; <= captured"),
        F("updated_at", "ts", rule=">= created_at"),
    ]),
    "order_status_history": ("Append-only order lifecycle transitions.", "history_id", [
        F("history_id", "text", unique=True, pattern=PATTERNS["order_history_id"]),
        F("payment_id", "text", fk="payment_orders.payment_id"),
        F("from_status", "text", required=False, allowed=ORDER_STATUS),
        F("to_status", "text", allowed=ORDER_STATUS, rule="must be an allowed transition"),
        F("changed_at", "ts"),
        F("cause_event_id", "text", required=False, fk="processor_events.event_id"),
    ]),
    "payment_attempts": ("Authorisation attempts; retries share the order.", "attempt_id", [
        F("attempt_id", "text", unique=True, pattern=PATTERNS["attempt_id"]),
        F("payment_id", "text", fk="payment_orders.payment_id"),
        F("attempt_no", "int", allowed=(1, 2, 3)),
        F("created_at", "ts", rule=">= order created_at"),
        F("status", "text", allowed=("SUCCEEDED", "FAILED")),
        F("failure_code", "text", required=False, rule="required when status = FAILED"),
        F("processor", "text", allowed=("NOVAPAY",)),
    ]),
    "processor_events": ("Processor's canonical event registry (one row per real event).", "event_id", [
        F("event_id", "text", unique=True, pattern=PATTERNS["event_id"]),
        F("payment_id", "text", fk="payment_orders.payment_id"),
        F("attempt_id", "text", fk="payment_attempts.attempt_id"),
        F("event_type", "text", allowed=EVENT_TYPES),
        F("amount_minor", "int", unit=MINOR, rule="> 0"),
        F("currency", "text", allowed=CCY),
        F("occurred_at", "ts"),
    ]),
    "webhook_deliveries": ("Raw webhook ingestion log; may contain duplicate deliveries.", "delivery_id", [
        F("delivery_id", "text", unique=True, pattern=PATTERNS["delivery_id"]),
        F("received_at", "ts", rule=">= occurred_at"),
        F("event_id", "text", fk="processor_events.event_id", rule="not unique here (duplicates)"),
        F("payment_id", "text", fk="payment_orders.payment_id"),
        F("attempt_id", "text", fk="payment_attempts.attempt_id"),
        F("event_type", "text", allowed=EVENT_TYPES),
        F("amount_minor", "int", unit=MINOR),
        F("currency", "text", allowed=CCY),
        F("occurred_at", "ts"),
    ]),
    "settlement_batches": ("Processor settlement batch per currency per day; totals derived from lines.", "batch_id", [
        F("batch_id", "text", unique=True, pattern=PATTERNS["batch_id"]),
        F("processor", "text", allowed=("NOVAPAY",)),
        F("currency", "text", allowed=CCY),
        F("settlement_date", "date"),
        F("status", "text", allowed=("CLOSED",)),
        F("created_at", "ts"),
        F("line_count", "int", rule="= count(lines)"),
        F("gross_capture_minor", "int", unit=MINOR, rule="= sum capture gross"),
        F("gross_refund_minor", "int", unit=MINOR, rule="= sum refund gross"),
        F("fee_minor", "int", unit=MINOR, rule="= sum line fees"),
        F("net_minor", "int", unit=MINOR, rule="= gross_capture - gross_refund - fee"),
    ]),
    "settlement_lines": ("One line per settled capture/refund.", "settlement_line_id", [
        F("settlement_line_id", "text", unique=True, pattern=PATTERNS["settlement_line_id"]),
        F("batch_id", "text", fk="settlement_batches.batch_id"),
        F("event_id", "text", fk="processor_events.event_id"),
        F("payment_id", "text", fk="payment_orders.payment_id"),
        F("merchant_id", "text", fk="merchants.merchant_id"),
        F("line_type", "text", allowed=("CAPTURE", "REFUND")),
        F("gross_minor", "int", unit=MINOR, rule="> 0"),
        F("fee_minor", "int", unit=MINOR, rule="capture: fee schedule in force on capture date; refund: 0"),
        F("net_minor", "int", unit=MINOR, rule="capture: gross-fee; refund: -gross"),
        F("currency", "text", allowed=CCY),
    ]),
    "bank_statement_lines": ("Bank account statement (processor payouts + unrelated activity).", "bank_line_id", [
        F("bank_line_id", "text", unique=True, pattern=PATTERNS["bank_line_id"]),
        F("account_id", "text", pattern=r"^ACC-[A-Z]{3}-\d{3}$"),
        F("value_date", "date"),
        F("booking_date", "date", rule=">= value_date"),
        F("direction", "text", allowed=("CREDIT", "DEBIT")),
        F("amount_minor", "int", unit=MINOR, rule="> 0; sign from direction"),
        F("currency", "text", allowed=CCY),
        F("counterparty", "text"),
        F("reference", "text", required=False),
        F("description", "text"),
        F("transaction_code", "text", allowed=("CREDIT_TRANSFER", "DEBIT_TRANSFER", "BANK_CHARGE", "INTEREST")),
    ]),
    "canonical_events": ("Engine output: deduplicated events (one per event_id) built from webhook_deliveries.", "event_id", [
        F("event_id", "text", unique=True, pattern=PATTERNS["event_id"], fk="processor_events.event_id"),
        F("payment_id", "text", fk="payment_orders.payment_id"),
        F("attempt_id", "text", fk="payment_attempts.attempt_id"),
        F("event_type", "text", allowed=EVENT_TYPES),
        F("amount_minor", "int", unit=MINOR),
        F("currency", "text", allowed=CCY),
        F("occurred_at", "ts"),
        F("first_delivery_id", "text", fk="webhook_deliveries.delivery_id", rule="earliest received delivery wins"),
        F("first_received_at", "ts"),
    ]),
    "item_status": ("Engine output: one reconciliation status per in-scope record (coverage proof).", "item_type,item_id", [
        F("item_type", "text", allowed=ENTITY_TYPES),
        F("item_id", "text", rule="polymorphic FK to item_type's table"),
        F("recon_status", "text", allowed=("MATCHED", "PARTIAL", "EXCEPTION", "IN_TRANSIT", "OUT_OF_PERIOD", "OUT_OF_SCOPE")),
        F("reason", "text", rule="rule id or exception type that decided the status"),
    ]),
    "reconciliation_matches": ("Engine match decisions (header).", "match_id", [
        F("match_id", "text", unique=True, pattern=PATTERNS["match_id"]),
        F("match_level", "text", allowed=("EVENT_TO_SETTLEMENT", "BATCH_TO_BANK")),
        F("match_type", "text", allowed=("EXACT", "WITHIN_TOLERANCE", "SPLIT", "FUZZY", "PARTIAL")),
        F("status", "text", allowed=("MATCHED", "PARTIAL")),
        F("rule_id", "text"),
        F("left_amount_minor", "int", unit=MINOR),
        F("right_amount_minor", "int", unit=MINOR),
        F("difference_minor", "int", unit=MINOR, rule="= right - left; |diff| <= tolerance when MATCHED"),
        F("currency", "text", allowed=CCY),
        F("decided_at", "ts"),
        F("decided_by", "text"),
    ]),
    "match_items": ("Bridge table (N:M) linking a match to the records on each side.", "match_id,entity_type,entity_id", [
        F("match_id", "text", fk="reconciliation_matches.match_id"),
        F("entity_type", "text", allowed=ENTITY_TYPES),
        F("entity_id", "text", rule="polymorphic FK to entity_type's table"),
        F("side", "text", allowed=("LEFT", "RIGHT")),
    ]),
    "exceptions": ("Every unmatched / partial / invalid item.", "exception_id", [
        F("exception_id", "text", unique=True, pattern=PATTERNS["exception_id"]),
        F("exception_type", "text", allowed=tuple(EXCEPTIONS)),
        F("severity", "text", allowed=("LOW", "MEDIUM", "HIGH", "CRITICAL")),
        F("owner_role", "text", allowed=ROLES),
        F("entity_type", "text", allowed=ENTITY_TYPES),
        F("entity_id", "text", rule="polymorphic FK to entity_type's table"),
        F("related_ids", "text", required=False, rule="pipe-separated trace ids"),
        F("amount_minor", "int", required=False, unit=MINOR),
        F("currency", "text", required=False, allowed=CCY),
        F("rule_id", "text"),
        F("description", "text"),
        F("detected_at", "ts"),
        F("status", "text", allowed=("OPEN", "IN_REVIEW", "ESCALATED", "RESOLVED"),
          rule="derived: latest exception_status_history row"),
    ]),
    "exception_status_history": ("Append-only exception workflow.", "history_id", [
        F("history_id", "text", unique=True, pattern=PATTERNS["exception_history_id"]),
        F("exception_id", "text", fk="exceptions.exception_id"),
        F("from_status", "text", required=False),
        F("to_status", "text", allowed=("OPEN", "IN_REVIEW", "ESCALATED", "RESOLVED")),
        F("changed_at", "ts"),
        F("actor_role", "text", allowed=ROLES),
    ]),
    "resolutions": ("Resolution recorded against an exception (0..1 per exception).", "resolution_id", [
        F("resolution_id", "text", unique=True, pattern=PATTERNS["resolution_id"]),
        F("exception_id", "text", unique=True, fk="exceptions.exception_id"),
        F("resolution_type", "text"),
        F("resolved_by_role", "text", allowed=ROLES),
        F("resolved_at", "ts", rule=">= exception detected_at"),
        F("adjustment_amount_minor", "int", unit=MINOR),
        F("currency", "text", required=False, allowed=CCY),
        F("notes", "text"),
    ]),
}

OUTPUT_TABLES = ["reconciliation_matches", "match_items", "exceptions", "exception_status_history", "resolutions"]
