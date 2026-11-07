"""Shared SQL. Exception status is always derived from the latest history row (never stored/edited)."""

EXCEPTION_COLS = ("e.exception_id, e.exception_type, e.severity, e.owner_role, e.entity_type, e.entity_id, "
                  "e.related_ids, e.amount_minor, e.currency, e.rule_id, e.description, e.detected_at")

EXCEPTIONS_LIVE = f"""
WITH latest AS (
  SELECT exception_id, MAX(history_id) AS hid FROM exception_status_history GROUP BY exception_id
)
SELECT {EXCEPTION_COLS}, h.to_status AS status, h.changed_at AS status_changed_at, h.actor_role AS status_actor
FROM exceptions e
JOIN latest l ON l.exception_id = e.exception_id
JOIN exception_status_history h ON h.history_id = l.hid
"""

ENTITY_TABLE = {
    "PAYMENT_ORDER": ("payment_orders", "payment_id"),
    "PROCESSOR_EVENT": ("canonical_events", "event_id"),
    "WEBHOOK_DELIVERY": ("webhook_deliveries", "delivery_id"),
    "SETTLEMENT_BATCH": ("settlement_batches", "batch_id"),
    "SETTLEMENT_LINE": ("settlement_lines", "settlement_line_id"),
    "BANK_LINE": ("bank_statement_lines", "bank_line_id"),
}

PREFIX_TYPE = [("PAY-", "PAYMENT_ORDER"), ("EVT-", "PROCESSOR_EVENT"), ("DLV-", "WEBHOOK_DELIVERY"),
               ("STL-", "SETTLEMENT_LINE"), ("SET-", "SETTLEMENT_BATCH"), ("BANK-", "BANK_LINE")]


def entity_type_of(entity_id: str):
    return next((t for p, t in PREFIX_TYPE if entity_id.startswith(p)), None)
