-- Generated from recon/schema.py. Portable: PostgreSQL (primary) and SQLite.

-- Merchant master data (effective-dated fee terms).
CREATE TABLE merchants (
  merchant_id TEXT NOT NULL,
  legal_name TEXT NOT NULL,
  country TEXT NOT NULL CHECK (country IN ('US', 'DE', 'FR', 'ES', 'IT', 'NL', 'GB', 'IN', 'JP')),
  settlement_currency TEXT NOT NULL CHECK (settlement_currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  mcc TEXT NOT NULL,
  risk_tier TEXT NOT NULL CHECK (risk_tier IN ('LOW', 'MEDIUM', 'HIGH')),
  settlement_delay_days BIGINT NOT NULL CHECK (settlement_delay_days IN (1, 2, 3)),
  status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'SUSPENDED')),
  onboarded_on DATE NOT NULL,
  effective_from DATE NOT NULL,
  effective_to DATE,
  PRIMARY KEY (merchant_id)
);

-- Effective-dated fee terms (SCD type 2). Fee applied = version in force on the capture date.
CREATE TABLE merchant_fee_schedules (
  fee_schedule_id TEXT NOT NULL,
  merchant_id TEXT NOT NULL,
  version BIGINT NOT NULL,
  fee_rate_bps BIGINT NOT NULL,
  fixed_fee_minor BIGINT NOT NULL,
  effective_from DATE NOT NULL,
  effective_to DATE,
  PRIMARY KEY (fee_schedule_id),
  FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

-- Customer payment order; status derived from events.
CREATE TABLE payment_orders (
  payment_id TEXT NOT NULL,
  merchant_id TEXT NOT NULL,
  customer_ref TEXT NOT NULL,
  amount_minor BIGINT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  payment_method TEXT NOT NULL CHECK (payment_method IN ('CARD', 'WALLET', 'BANK_TRANSFER')),
  created_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('CREATED', 'AUTHORIZED', 'CAPTURED', 'PARTIALLY_REFUNDED', 'REFUNDED', 'FAILED', 'VOIDED')),
  captured_amount_minor BIGINT NOT NULL,
  refunded_amount_minor BIGINT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (payment_id),
  FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

-- Authorisation attempts; retries share the order.
CREATE TABLE payment_attempts (
  attempt_id TEXT NOT NULL,
  payment_id TEXT NOT NULL,
  attempt_no BIGINT NOT NULL CHECK (attempt_no IN (1, 2, 3)),
  created_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('SUCCEEDED', 'FAILED')),
  failure_code TEXT,
  processor TEXT NOT NULL CHECK (processor IN ('NOVAPAY')),
  PRIMARY KEY (attempt_id),
  FOREIGN KEY (payment_id) REFERENCES payment_orders(payment_id)
);

-- Processor's canonical event registry (one row per real event).
CREATE TABLE processor_events (
  event_id TEXT NOT NULL,
  payment_id TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('payment.authorized', 'payment.captured', 'payment.refunded', 'payment.failed', 'payment.voided')),
  amount_minor BIGINT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  occurred_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (event_id),
  FOREIGN KEY (payment_id) REFERENCES payment_orders(payment_id),
  FOREIGN KEY (attempt_id) REFERENCES payment_attempts(attempt_id)
);

-- Append-only order lifecycle transitions.
CREATE TABLE order_status_history (
  history_id TEXT NOT NULL,
  payment_id TEXT NOT NULL,
  from_status TEXT CHECK (from_status IN ('CREATED', 'AUTHORIZED', 'CAPTURED', 'PARTIALLY_REFUNDED', 'REFUNDED', 'FAILED', 'VOIDED')),
  to_status TEXT NOT NULL CHECK (to_status IN ('CREATED', 'AUTHORIZED', 'CAPTURED', 'PARTIALLY_REFUNDED', 'REFUNDED', 'FAILED', 'VOIDED')),
  changed_at TIMESTAMPTZ NOT NULL,
  cause_event_id TEXT,
  PRIMARY KEY (history_id),
  FOREIGN KEY (payment_id) REFERENCES payment_orders(payment_id),
  FOREIGN KEY (cause_event_id) REFERENCES processor_events(event_id)
);

-- Raw webhook ingestion log; may contain duplicate deliveries.
CREATE TABLE webhook_deliveries (
  delivery_id TEXT NOT NULL,
  received_at TIMESTAMPTZ NOT NULL,
  event_id TEXT NOT NULL,
  payment_id TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('payment.authorized', 'payment.captured', 'payment.refunded', 'payment.failed', 'payment.voided')),
  amount_minor BIGINT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  occurred_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (delivery_id),
  FOREIGN KEY (event_id) REFERENCES processor_events(event_id),
  FOREIGN KEY (payment_id) REFERENCES payment_orders(payment_id),
  FOREIGN KEY (attempt_id) REFERENCES payment_attempts(attempt_id)
);

-- Processor settlement batch per currency per day; totals derived from lines.
CREATE TABLE settlement_batches (
  batch_id TEXT NOT NULL,
  processor TEXT NOT NULL CHECK (processor IN ('NOVAPAY')),
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  settlement_date DATE NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('CLOSED')),
  created_at TIMESTAMPTZ NOT NULL,
  line_count BIGINT NOT NULL,
  gross_capture_minor BIGINT NOT NULL,
  gross_refund_minor BIGINT NOT NULL,
  fee_minor BIGINT NOT NULL,
  net_minor BIGINT NOT NULL,
  PRIMARY KEY (batch_id)
);

-- One line per settled capture/refund.
CREATE TABLE settlement_lines (
  settlement_line_id TEXT NOT NULL,
  batch_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  payment_id TEXT NOT NULL,
  merchant_id TEXT NOT NULL,
  line_type TEXT NOT NULL CHECK (line_type IN ('CAPTURE', 'REFUND')),
  gross_minor BIGINT NOT NULL,
  fee_minor BIGINT NOT NULL,
  net_minor BIGINT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  PRIMARY KEY (settlement_line_id),
  FOREIGN KEY (batch_id) REFERENCES settlement_batches(batch_id),
  FOREIGN KEY (event_id) REFERENCES processor_events(event_id),
  FOREIGN KEY (payment_id) REFERENCES payment_orders(payment_id),
  FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);

-- Bank account statement (processor payouts + unrelated activity).
CREATE TABLE bank_statement_lines (
  bank_line_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  value_date DATE NOT NULL,
  booking_date DATE NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('CREDIT', 'DEBIT')),
  amount_minor BIGINT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  counterparty TEXT NOT NULL,
  reference TEXT,
  description TEXT NOT NULL,
  transaction_code TEXT NOT NULL CHECK (transaction_code IN ('CREDIT_TRANSFER', 'DEBIT_TRANSFER', 'BANK_CHARGE', 'INTEREST')),
  PRIMARY KEY (bank_line_id)
);

-- Engine output: deduplicated events (one per event_id) built from webhook_deliveries.
CREATE TABLE canonical_events (
  event_id TEXT NOT NULL,
  payment_id TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('payment.authorized', 'payment.captured', 'payment.refunded', 'payment.failed', 'payment.voided')),
  amount_minor BIGINT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  occurred_at TIMESTAMPTZ NOT NULL,
  first_delivery_id TEXT NOT NULL,
  first_received_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (event_id),
  FOREIGN KEY (event_id) REFERENCES processor_events(event_id),
  FOREIGN KEY (payment_id) REFERENCES payment_orders(payment_id),
  FOREIGN KEY (attempt_id) REFERENCES payment_attempts(attempt_id),
  FOREIGN KEY (first_delivery_id) REFERENCES webhook_deliveries(delivery_id)
);

-- Engine output: one reconciliation status per in-scope record (coverage proof).
CREATE TABLE item_status (
  item_type TEXT NOT NULL CHECK (item_type IN ('PAYMENT_ORDER', 'PROCESSOR_EVENT', 'WEBHOOK_DELIVERY', 'SETTLEMENT_BATCH', 'SETTLEMENT_LINE', 'BANK_LINE')),
  item_id TEXT NOT NULL,
  recon_status TEXT NOT NULL CHECK (recon_status IN ('MATCHED', 'PARTIAL', 'EXCEPTION', 'IN_TRANSIT', 'OUT_OF_PERIOD', 'OUT_OF_SCOPE')),
  reason TEXT NOT NULL,
  PRIMARY KEY (item_type,item_id)
);

-- Engine match decisions (header).
CREATE TABLE reconciliation_matches (
  match_id TEXT NOT NULL,
  match_level TEXT NOT NULL CHECK (match_level IN ('EVENT_TO_SETTLEMENT', 'BATCH_TO_BANK')),
  match_type TEXT NOT NULL CHECK (match_type IN ('EXACT', 'WITHIN_TOLERANCE', 'SPLIT', 'FUZZY', 'PARTIAL')),
  status TEXT NOT NULL CHECK (status IN ('MATCHED', 'PARTIAL')),
  rule_id TEXT NOT NULL,
  left_amount_minor BIGINT NOT NULL,
  right_amount_minor BIGINT NOT NULL,
  difference_minor BIGINT NOT NULL,
  currency TEXT NOT NULL CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  decided_at TIMESTAMPTZ NOT NULL,
  decided_by TEXT NOT NULL,
  PRIMARY KEY (match_id)
);

-- Bridge table (N:M) linking a match to the records on each side.
CREATE TABLE match_items (
  match_id TEXT NOT NULL,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('PAYMENT_ORDER', 'PROCESSOR_EVENT', 'WEBHOOK_DELIVERY', 'SETTLEMENT_BATCH', 'SETTLEMENT_LINE', 'BANK_LINE')),
  entity_id TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('LEFT', 'RIGHT')),
  PRIMARY KEY (match_id,entity_type,entity_id),
  FOREIGN KEY (match_id) REFERENCES reconciliation_matches(match_id)
);

-- Every unmatched / partial / invalid item.
CREATE TABLE exceptions (
  exception_id TEXT NOT NULL,
  exception_type TEXT NOT NULL CHECK (exception_type IN ('DUPLICATE_WEBHOOK', 'WEBHOOK_PAYLOAD_CONFLICT', 'ORPHAN_EVENT', 'REFUND_BEFORE_CAPTURE', 'REFUND_WITHOUT_CAPTURE', 'OVER_REFUND', 'DUPLICATE_SETTLEMENT_LINE', 'MISSING_SETTLEMENT_LINE', 'ORPHAN_SETTLEMENT_LINE', 'SETTLEMENT_AMOUNT_MISMATCH', 'FEE_RULE_VIOLATION', 'BATCH_TOTAL_MISMATCH', 'FEE_DIFFERENCE', 'BANK_AMOUNT_MISMATCH', 'CURRENCY_MISMATCH', 'PAYOUT_OUTSIDE_DATE_WINDOW', 'UNMATCHED_SETTLEMENT_BATCH', 'UNMATCHED_BANK_LINE', 'AMBIGUOUS_BANK_MATCH')),
  severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
  owner_role TEXT NOT NULL CHECK (owner_role IN ('SYSTEM', 'OPS_ANALYST', 'RISK_REVIEWER')),
  entity_type TEXT NOT NULL CHECK (entity_type IN ('PAYMENT_ORDER', 'PROCESSOR_EVENT', 'WEBHOOK_DELIVERY', 'SETTLEMENT_BATCH', 'SETTLEMENT_LINE', 'BANK_LINE')),
  entity_id TEXT NOT NULL,
  related_ids TEXT,
  amount_minor BIGINT,
  currency TEXT CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  rule_id TEXT NOT NULL,
  description TEXT NOT NULL,
  detected_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('OPEN', 'IN_REVIEW', 'ESCALATED', 'RESOLVED')),
  PRIMARY KEY (exception_id)
);

-- Append-only exception workflow.
CREATE TABLE exception_status_history (
  history_id TEXT NOT NULL,
  exception_id TEXT NOT NULL,
  from_status TEXT,
  to_status TEXT NOT NULL CHECK (to_status IN ('OPEN', 'IN_REVIEW', 'ESCALATED', 'RESOLVED')),
  changed_at TIMESTAMPTZ NOT NULL,
  actor_role TEXT NOT NULL CHECK (actor_role IN ('SYSTEM', 'OPS_ANALYST', 'RISK_REVIEWER')),
  PRIMARY KEY (history_id),
  FOREIGN KEY (exception_id) REFERENCES exceptions(exception_id)
);

-- Resolution recorded against an exception (0..1 per exception).
CREATE TABLE resolutions (
  resolution_id TEXT NOT NULL,
  exception_id TEXT NOT NULL UNIQUE,
  resolution_type TEXT NOT NULL,
  resolved_by_role TEXT NOT NULL CHECK (resolved_by_role IN ('SYSTEM', 'OPS_ANALYST', 'RISK_REVIEWER')),
  resolved_at TIMESTAMPTZ NOT NULL,
  adjustment_amount_minor BIGINT NOT NULL,
  currency TEXT CHECK (currency IN ('USD', 'EUR', 'GBP', 'INR', 'JPY')),
  notes TEXT NOT NULL,
  PRIMARY KEY (resolution_id),
  FOREIGN KEY (exception_id) REFERENCES exceptions(exception_id)
);

CREATE INDEX idx_merchant_fee_schedules_merchant_id ON merchant_fee_schedules (merchant_id);
CREATE INDEX idx_payment_orders_merchant_id ON payment_orders (merchant_id);
CREATE INDEX idx_payment_attempts_payment_id ON payment_attempts (payment_id);
CREATE INDEX idx_processor_events_payment_id ON processor_events (payment_id);
CREATE INDEX idx_canonical_events_payment_id ON canonical_events (payment_id);
CREATE INDEX idx_webhook_deliveries_payment_id ON webhook_deliveries (payment_id);
CREATE INDEX idx_order_status_history_payment_id ON order_status_history (payment_id);
CREATE INDEX idx_settlement_lines_batch_id ON settlement_lines (batch_id);
CREATE INDEX idx_settlement_lines_payment_id ON settlement_lines (payment_id);
CREATE INDEX idx_settlement_lines_event_id ON settlement_lines (event_id);
CREATE INDEX idx_match_items_entity_id ON match_items (entity_id);
CREATE INDEX idx_item_status_item_id ON item_status (item_id);
CREATE INDEX idx_exceptions_entity_id ON exceptions (entity_id);
CREATE INDEX idx_exception_status_history_exception_id ON exception_status_history (exception_id);
