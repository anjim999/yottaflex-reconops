# Data dictionary

Generated from `recon/schema.py` by `python -m recon docs`. All money is integer **minor units** (cents, paise; JPY has 0 decimals). All timestamps are UTC.

## `merchants`

Merchant master data (effective-dated fee terms).

Primary key: `merchant_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `merchant_id` | string | yes |  |  | yes | regex `^MER-\d{6}$` |
| `legal_name` | string | yes |  |  |  |  |
| `country` | string | yes | US, DE, FR, ES, IT, NL, GB, IN, JP |  |  |  |
| `settlement_currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |
| `mcc` | string | yes |  |  |  | ISO 18245 merchant category code |
| `risk_tier` | string | yes | LOW, MEDIUM, HIGH |  |  |  |
| `settlement_delay_days` | integer | yes | 1, 2, 3 | days |  |  |
| `status` | string | yes | ACTIVE, SUSPENDED |  |  |  |
| `onboarded_on` | date (YYYY-MM-DD) | yes |  |  |  |  |
| `effective_from` | date (YYYY-MM-DD) | yes |  |  |  | merchant record valid from |
| `effective_to` | date (YYYY-MM-DD) | no |  |  |  | null = current; >= effective_from |

## `merchant_fee_schedules`

Effective-dated fee terms (SCD type 2). Fee applied = version in force on the capture date.

Primary key: `fee_schedule_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `fee_schedule_id` | string | yes |  |  | yes | regex `^FEE-\d{6}$` |
| `merchant_id` | string | yes |  |  |  | FK -> `merchants.merchant_id` |
| `version` | integer | yes |  |  |  | 1..n per merchant, contiguous |
| `fee_rate_bps` | integer | yes |  | basis points |  | 100-400 |
| `fixed_fee_minor` | integer | yes |  | minor currency units |  | >= 0 |
| `effective_from` | date (YYYY-MM-DD) | yes |  |  |  | v1 = onboarding date; v(n+1) = v(n).effective_to + 1 day |
| `effective_to` | date (YYYY-MM-DD) | no |  |  |  | null = current version; no gaps or overlaps |

## `payment_orders`

Customer payment order; status derived from events.

Primary key: `payment_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `payment_id` | string | yes |  |  | yes | regex `^PAY-2026-\d{8}$` |
| `merchant_id` | string | yes |  |  |  | FK -> `merchants.merchant_id` |
| `customer_ref` | string | yes |  |  |  | regex `^CUS-\d{7}$`; pseudonymous synthetic customer |
| `amount_minor` | integer | yes |  | minor currency units |  | > 0 |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  | = merchant settlement_currency |
| `payment_method` | string | yes | CARD, WALLET, BANK_TRANSFER |  |  |  |
| `created_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |
| `status` | string | yes | CREATED, AUTHORIZED, CAPTURED, PARTIALLY_REFUNDED, REFUNDED, FAILED, VOIDED |  |  | derived: last order_status_history row |
| `captured_amount_minor` | integer | yes |  | minor currency units |  | derived: sum of capture events |
| `refunded_amount_minor` | integer | yes |  | minor currency units |  | derived: sum of refunds; <= captured |
| `updated_at` | timestamp (ISO-8601 UTC) | yes |  |  |  | >= created_at |

## `order_status_history`

Append-only order lifecycle transitions.

Primary key: `history_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `history_id` | string | yes |  |  | yes | regex `^OSH-2026-\d{8}$` |
| `payment_id` | string | yes |  |  |  | FK -> `payment_orders.payment_id` |
| `from_status` | string | no | CREATED, AUTHORIZED, CAPTURED, PARTIALLY_REFUNDED, REFUNDED, FAILED, VOIDED |  |  |  |
| `to_status` | string | yes | CREATED, AUTHORIZED, CAPTURED, PARTIALLY_REFUNDED, REFUNDED, FAILED, VOIDED |  |  | must be an allowed transition |
| `changed_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |
| `cause_event_id` | string | no |  |  |  | FK -> `processor_events.event_id` |

## `payment_attempts`

Authorisation attempts; retries share the order.

Primary key: `attempt_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `attempt_id` | string | yes |  |  | yes | regex `^ATT-PAY-2026-\d{8}-\d{2}$` |
| `payment_id` | string | yes |  |  |  | FK -> `payment_orders.payment_id` |
| `attempt_no` | integer | yes | 1, 2, 3 |  |  |  |
| `created_at` | timestamp (ISO-8601 UTC) | yes |  |  |  | >= order created_at |
| `status` | string | yes | SUCCEEDED, FAILED |  |  |  |
| `failure_code` | string | no |  |  |  | required when status = FAILED |
| `processor` | string | yes | NOVAPAY |  |  |  |

## `processor_events`

Processor's canonical event registry (one row per real event).

Primary key: `event_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `event_id` | string | yes |  |  | yes | regex `^EVT-2026-\d{8}$` |
| `payment_id` | string | yes |  |  |  | FK -> `payment_orders.payment_id` |
| `attempt_id` | string | yes |  |  |  | FK -> `payment_attempts.attempt_id` |
| `event_type` | string | yes | payment.authorized, payment.captured, payment.refunded, payment.failed, payment.voided |  |  |  |
| `amount_minor` | integer | yes |  | minor currency units |  | > 0 |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |
| `occurred_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |

## `webhook_deliveries`

Raw webhook ingestion log; may contain duplicate deliveries.

Primary key: `delivery_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `delivery_id` | string | yes |  |  | yes | regex `^DLV-2026-\d{8}$` |
| `received_at` | timestamp (ISO-8601 UTC) | yes |  |  |  | >= occurred_at |
| `event_id` | string | yes |  |  |  | FK -> `processor_events.event_id`; not unique here (duplicates) |
| `payment_id` | string | yes |  |  |  | FK -> `payment_orders.payment_id` |
| `attempt_id` | string | yes |  |  |  | FK -> `payment_attempts.attempt_id` |
| `event_type` | string | yes | payment.authorized, payment.captured, payment.refunded, payment.failed, payment.voided |  |  |  |
| `amount_minor` | integer | yes |  | minor currency units |  |  |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |
| `occurred_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |

## `settlement_batches`

Processor settlement batch per currency per day; totals derived from lines.

Primary key: `batch_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `batch_id` | string | yes |  |  | yes | regex `^SET-2026-\d{6}$` |
| `processor` | string | yes | NOVAPAY |  |  |  |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |
| `settlement_date` | date (YYYY-MM-DD) | yes |  |  |  |  |
| `status` | string | yes | CLOSED |  |  |  |
| `created_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |
| `line_count` | integer | yes |  |  |  | = count(lines) |
| `gross_capture_minor` | integer | yes |  | minor currency units |  | = sum capture gross |
| `gross_refund_minor` | integer | yes |  | minor currency units |  | = sum refund gross |
| `fee_minor` | integer | yes |  | minor currency units |  | = sum line fees |
| `net_minor` | integer | yes |  | minor currency units |  | = gross_capture - gross_refund - fee |

## `settlement_lines`

One line per settled capture/refund.

Primary key: `settlement_line_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `settlement_line_id` | string | yes |  |  | yes | regex `^STL-SET-2026-\d{6}-\d{3}$` |
| `batch_id` | string | yes |  |  |  | FK -> `settlement_batches.batch_id` |
| `event_id` | string | yes |  |  |  | FK -> `processor_events.event_id` |
| `payment_id` | string | yes |  |  |  | FK -> `payment_orders.payment_id` |
| `merchant_id` | string | yes |  |  |  | FK -> `merchants.merchant_id` |
| `line_type` | string | yes | CAPTURE, REFUND |  |  |  |
| `gross_minor` | integer | yes |  | minor currency units |  | > 0 |
| `fee_minor` | integer | yes |  | minor currency units |  | capture: fee schedule in force on capture date; refund: 0 |
| `net_minor` | integer | yes |  | minor currency units |  | capture: gross-fee; refund: -gross |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |

## `bank_statement_lines`

Bank account statement (processor payouts + unrelated activity).

Primary key: `bank_line_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `bank_line_id` | string | yes |  |  | yes | regex `^BANK-2026-\d{6}$` |
| `account_id` | string | yes |  |  |  | regex `^ACC-[A-Z]{3}-\d{3}$` |
| `value_date` | date (YYYY-MM-DD) | yes |  |  |  |  |
| `booking_date` | date (YYYY-MM-DD) | yes |  |  |  | >= value_date |
| `direction` | string | yes | CREDIT, DEBIT |  |  |  |
| `amount_minor` | integer | yes |  | minor currency units |  | > 0; sign from direction |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |
| `counterparty` | string | yes |  |  |  |  |
| `reference` | string | no |  |  |  |  |
| `description` | string | yes |  |  |  |  |
| `transaction_code` | string | yes | CREDIT_TRANSFER, DEBIT_TRANSFER, BANK_CHARGE, INTEREST |  |  |  |

## `canonical_events`

Engine output: deduplicated events (one per event_id) built from webhook_deliveries.

Primary key: `event_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `event_id` | string | yes |  |  | yes | FK -> `processor_events.event_id`; regex `^EVT-2026-\d{8}$` |
| `payment_id` | string | yes |  |  |  | FK -> `payment_orders.payment_id` |
| `attempt_id` | string | yes |  |  |  | FK -> `payment_attempts.attempt_id` |
| `event_type` | string | yes | payment.authorized, payment.captured, payment.refunded, payment.failed, payment.voided |  |  |  |
| `amount_minor` | integer | yes |  | minor currency units |  |  |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |
| `occurred_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |
| `first_delivery_id` | string | yes |  |  |  | FK -> `webhook_deliveries.delivery_id`; earliest received delivery wins |
| `first_received_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |

## `item_status`

Engine output: one reconciliation status per in-scope record (coverage proof).

Primary key: `item_type,item_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `item_type` | string | yes | PAYMENT_ORDER, PROCESSOR_EVENT, WEBHOOK_DELIVERY, SETTLEMENT_BATCH, SETTLEMENT_LINE, BANK_LINE |  |  |  |
| `item_id` | string | yes |  |  |  | polymorphic FK to item_type's table |
| `recon_status` | string | yes | MATCHED, PARTIAL, EXCEPTION, IN_TRANSIT, OUT_OF_PERIOD, OUT_OF_SCOPE |  |  |  |
| `reason` | string | yes |  |  |  | rule id or exception type that decided the status |

## `reconciliation_matches`

Engine match decisions (header).

Primary key: `match_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `match_id` | string | yes |  |  | yes | regex `^REC-2026-\d{6}$` |
| `match_level` | string | yes | EVENT_TO_SETTLEMENT, BATCH_TO_BANK |  |  |  |
| `match_type` | string | yes | EXACT, WITHIN_TOLERANCE, SPLIT, FUZZY, PARTIAL |  |  |  |
| `status` | string | yes | MATCHED, PARTIAL |  |  |  |
| `rule_id` | string | yes |  |  |  |  |
| `left_amount_minor` | integer | yes |  | minor currency units |  |  |
| `right_amount_minor` | integer | yes |  | minor currency units |  |  |
| `difference_minor` | integer | yes |  | minor currency units |  | = right - left; |diff| <= tolerance when MATCHED |
| `currency` | string | yes | USD, EUR, GBP, INR, JPY |  |  |  |
| `decided_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |
| `decided_by` | string | yes |  |  |  |  |

## `match_items`

Bridge table (N:M) linking a match to the records on each side.

Primary key: `match_id,entity_type,entity_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `match_id` | string | yes |  |  |  | FK -> `reconciliation_matches.match_id` |
| `entity_type` | string | yes | PAYMENT_ORDER, PROCESSOR_EVENT, WEBHOOK_DELIVERY, SETTLEMENT_BATCH, SETTLEMENT_LINE, BANK_LINE |  |  |  |
| `entity_id` | string | yes |  |  |  | polymorphic FK to entity_type's table |
| `side` | string | yes | LEFT, RIGHT |  |  |  |

## `exceptions`

Every unmatched / partial / invalid item.

Primary key: `exception_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `exception_id` | string | yes |  |  | yes | regex `^EXC-2026-\d{6}$` |
| `exception_type` | string | yes | 19 values (see schema) |  |  |  |
| `severity` | string | yes | LOW, MEDIUM, HIGH, CRITICAL |  |  |  |
| `owner_role` | string | yes | SYSTEM, OPS_ANALYST, RISK_REVIEWER |  |  |  |
| `entity_type` | string | yes | PAYMENT_ORDER, PROCESSOR_EVENT, WEBHOOK_DELIVERY, SETTLEMENT_BATCH, SETTLEMENT_LINE, BANK_LINE |  |  |  |
| `entity_id` | string | yes |  |  |  | polymorphic FK to entity_type's table |
| `related_ids` | string | no |  |  |  | pipe-separated trace ids |
| `amount_minor` | integer | no |  | minor currency units |  |  |
| `currency` | string | no | USD, EUR, GBP, INR, JPY |  |  |  |
| `rule_id` | string | yes |  |  |  |  |
| `description` | string | yes |  |  |  |  |
| `detected_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |
| `status` | string | yes | OPEN, IN_REVIEW, ESCALATED, RESOLVED |  |  | derived: latest exception_status_history row |

## `exception_status_history`

Append-only exception workflow.

Primary key: `history_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `history_id` | string | yes |  |  | yes | regex `^EXH-2026-\d{6}$` |
| `exception_id` | string | yes |  |  |  | FK -> `exceptions.exception_id` |
| `from_status` | string | no |  |  |  |  |
| `to_status` | string | yes | OPEN, IN_REVIEW, ESCALATED, RESOLVED |  |  |  |
| `changed_at` | timestamp (ISO-8601 UTC) | yes |  |  |  |  |
| `actor_role` | string | yes | SYSTEM, OPS_ANALYST, RISK_REVIEWER |  |  |  |

## `resolutions`

Resolution recorded against an exception (0..1 per exception).

Primary key: `resolution_id`

| Field | Type | Required | Allowed values | Unit | Unique | Validation / rule |
|---|---|---|---|---|---|---|
| `resolution_id` | string | yes |  |  | yes | regex `^RES-2026-\d{6}$` |
| `exception_id` | string | yes |  |  | yes | FK -> `exceptions.exception_id` |
| `resolution_type` | string | yes |  |  |  |  |
| `resolved_by_role` | string | yes | SYSTEM, OPS_ANALYST, RISK_REVIEWER |  |  |  |
| `resolved_at` | timestamp (ISO-8601 UTC) | yes |  |  |  | >= exception detected_at |
| `adjustment_amount_minor` | integer | yes |  | minor currency units |  |  |
| `currency` | string | no | USD, EUR, GBP, INR, JPY |  |  |  |
| `notes` | string | yes |  |  |  |  |
