# Validation summary

**274 checks, 274 passed, 0 failed.** Labelled (deliberately injected) anomalies are counted separately and are not failures.

| category | checks | failed |
|---|---|---|
| acceptance | 6 | 0 |
| arithmetic | 5 | 0 |
| consistency | 2 | 0 |
| date_ordering | 6 | 0 |
| duplicates | 2 | 0 |
| effective_dating | 4 | 0 |
| enum | 45 | 0 |
| foreign_key | 24 | 0 |
| id_format | 17 | 0 |
| lifecycle | 6 | 0 |
| primary_key | 17 | 0 |
| required | 134 | 0 |
| unique | 1 | 0 |
| volume | 5 | 0 |

## All checks

| category | check | table | checked | failures | labelled_anomalies | status | note |
|---|---|---|---|---|---|---|---|
| primary_key | unique, non-null (merchant_id) | merchants | 200 | 0 | 0 | PASS |  |
| required | merchant_id not null | merchants | 200 | 0 | 0 | PASS |  |
| id_format | merchant_id matches ^MER-\d{6}$ | merchants | 200 | 0 | 0 | PASS |  |
| required | legal_name not null | merchants | 200 | 0 | 0 | PASS |  |
| required | country not null | merchants | 200 | 0 | 0 | PASS |  |
| enum | country in allowed values | merchants | 200 | 0 | 0 | PASS |  |
| required | settlement_currency not null | merchants | 200 | 0 | 0 | PASS |  |
| enum | settlement_currency in allowed values | merchants | 200 | 0 | 0 | PASS |  |
| required | mcc not null | merchants | 200 | 0 | 0 | PASS |  |
| required | risk_tier not null | merchants | 200 | 0 | 0 | PASS |  |
| enum | risk_tier in allowed values | merchants | 200 | 0 | 0 | PASS |  |
| required | settlement_delay_days not null | merchants | 200 | 0 | 0 | PASS |  |
| enum | settlement_delay_days in allowed values | merchants | 200 | 0 | 0 | PASS |  |
| required | status not null | merchants | 200 | 0 | 0 | PASS |  |
| enum | status in allowed values | merchants | 200 | 0 | 0 | PASS |  |
| required | onboarded_on not null | merchants | 200 | 0 | 0 | PASS |  |
| required | effective_from not null | merchants | 200 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (fee_schedule_id) | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| required | fee_schedule_id not null | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| id_format | fee_schedule_id matches ^FEE-\d{6}$ | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| required | merchant_id not null | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| required | version not null | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| required | fee_rate_bps not null | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| required | fixed_fee_minor not null | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| required | effective_from not null | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (payment_id) | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | payment_id not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| id_format | payment_id matches ^PAY-2026-\d{8}$ | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | merchant_id not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | customer_ref not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| id_format | customer_ref matches ^CUS-\d{7}$ | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | amount_minor not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | currency not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| enum | currency in allowed values | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | payment_method not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| enum | payment_method in allowed values | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | created_at not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | status not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| enum | status in allowed values | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | captured_amount_minor not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | refunded_amount_minor not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| required | updated_at not null | payment_orders | 5000 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (history_id) | order_status_history | 15066 | 0 | 0 | PASS |  |
| required | history_id not null | order_status_history | 15066 | 0 | 0 | PASS |  |
| id_format | history_id matches ^OSH-2026-\d{8}$ | order_status_history | 15066 | 0 | 0 | PASS |  |
| required | payment_id not null | order_status_history | 15066 | 0 | 0 | PASS |  |
| enum | from_status in allowed values | order_status_history | 15066 | 0 | 0 | PASS |  |
| required | to_status not null | order_status_history | 15066 | 0 | 0 | PASS |  |
| enum | to_status in allowed values | order_status_history | 15066 | 0 | 0 | PASS |  |
| required | changed_at not null | order_status_history | 15066 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (attempt_id) | payment_attempts | 5500 | 0 | 0 | PASS |  |
| required | attempt_id not null | payment_attempts | 5500 | 0 | 0 | PASS |  |
| id_format | attempt_id matches ^ATT-PAY-2026-\d{8}-\d{2}$ | payment_attempts | 5500 | 0 | 0 | PASS |  |
| required | payment_id not null | payment_attempts | 5500 | 0 | 0 | PASS |  |
| required | attempt_no not null | payment_attempts | 5500 | 0 | 0 | PASS |  |
| enum | attempt_no in allowed values | payment_attempts | 5500 | 0 | 0 | PASS |  |
| required | created_at not null | payment_attempts | 5500 | 0 | 0 | PASS |  |
| required | status not null | payment_attempts | 5500 | 0 | 0 | PASS |  |
| enum | status in allowed values | payment_attempts | 5500 | 0 | 0 | PASS |  |
| required | processor not null | payment_attempts | 5500 | 0 | 0 | PASS |  |
| enum | processor in allowed values | payment_attempts | 5500 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (event_id) | processor_events | 10566 | 0 | 0 | PASS |  |
| required | event_id not null | processor_events | 10566 | 0 | 0 | PASS |  |
| id_format | event_id matches ^EVT-2026-\d{8}$ | processor_events | 10566 | 0 | 0 | PASS |  |
| required | payment_id not null | processor_events | 10566 | 0 | 0 | PASS |  |
| required | attempt_id not null | processor_events | 10566 | 0 | 0 | PASS |  |
| required | event_type not null | processor_events | 10566 | 0 | 0 | PASS |  |
| enum | event_type in allowed values | processor_events | 10566 | 0 | 0 | PASS |  |
| required | amount_minor not null | processor_events | 10566 | 0 | 0 | PASS |  |
| required | currency not null | processor_events | 10566 | 0 | 0 | PASS |  |
| enum | currency in allowed values | processor_events | 10566 | 0 | 0 | PASS |  |
| required | occurred_at not null | processor_events | 10566 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (delivery_id) | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | delivery_id not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| id_format | delivery_id matches ^DLV-2026-\d{8}$ | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | received_at not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | event_id not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | payment_id not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | attempt_id not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | event_type not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| enum | event_type in allowed values | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | amount_minor not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | currency not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| enum | currency in allowed values | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| required | occurred_at not null | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (batch_id) | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | batch_id not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| id_format | batch_id matches ^SET-2026-\d{6}$ | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | processor not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| enum | processor in allowed values | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | currency not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| enum | currency in allowed values | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | settlement_date not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | status not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| enum | status in allowed values | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | created_at not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | line_count not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | gross_capture_minor not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | gross_refund_minor not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | fee_minor not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| required | net_minor not null | settlement_batches | 100 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (settlement_line_id) | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | settlement_line_id not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| id_format | settlement_line_id matches ^STL-SET-2026-\d{6}-\d{3}$ | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | batch_id not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | event_id not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | payment_id not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | merchant_id not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | line_type not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| enum | line_type in allowed values | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | gross_minor not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | fee_minor not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | net_minor not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| required | currency not null | settlement_lines | 4298 | 0 | 0 | PASS |  |
| enum | currency in allowed values | settlement_lines | 4298 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (bank_line_id) | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | bank_line_id not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| id_format | bank_line_id matches ^BANK-2026-\d{6}$ | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | account_id not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| id_format | account_id matches ^ACC-[A-Z]{3}-\d{3}$ | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | value_date not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | booking_date not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | direction not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| enum | direction in allowed values | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | amount_minor not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | currency not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| enum | currency in allowed values | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | counterparty not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | description not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| required | transaction_code not null | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| enum | transaction_code in allowed values | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (event_id) | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | event_id not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| id_format | event_id matches ^EVT-2026-\d{8}$ | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | payment_id not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | attempt_id not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | event_type not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| enum | event_type in allowed values | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | amount_minor not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | currency not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| enum | currency in allowed values | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | occurred_at not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | first_delivery_id not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| required | first_received_at not null | canonical_events | 10566 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (item_type,item_id) | item_status | 10054 | 0 | 0 | PASS |  |
| required | item_type not null | item_status | 10054 | 0 | 0 | PASS |  |
| enum | item_type in allowed values | item_status | 10054 | 0 | 0 | PASS |  |
| required | item_id not null | item_status | 10054 | 0 | 0 | PASS |  |
| required | recon_status not null | item_status | 10054 | 0 | 0 | PASS |  |
| enum | recon_status in allowed values | item_status | 10054 | 0 | 0 | PASS |  |
| required | reason not null | item_status | 10054 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (match_id) | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | match_id not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| id_format | match_id matches ^REC-2026-\d{6}$ | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | match_level not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| enum | match_level in allowed values | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | match_type not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| enum | match_type in allowed values | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | status not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| enum | status in allowed values | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | rule_id not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | left_amount_minor not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | right_amount_minor not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | difference_minor not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | currency not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| enum | currency in allowed values | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | decided_at not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| required | decided_by not null | reconciliation_matches | 4392 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (match_id,entity_type,entity_id) | match_items | 8790 | 0 | 0 | PASS |  |
| required | match_id not null | match_items | 8790 | 0 | 0 | PASS |  |
| required | entity_type not null | match_items | 8790 | 0 | 0 | PASS |  |
| enum | entity_type in allowed values | match_items | 8790 | 0 | 0 | PASS |  |
| required | entity_id not null | match_items | 8790 | 0 | 0 | PASS |  |
| required | side not null | match_items | 8790 | 0 | 0 | PASS |  |
| enum | side in allowed values | match_items | 8790 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (exception_id) | exceptions | 190 | 0 | 0 | PASS |  |
| required | exception_id not null | exceptions | 190 | 0 | 0 | PASS |  |
| id_format | exception_id matches ^EXC-2026-\d{6}$ | exceptions | 190 | 0 | 0 | PASS |  |
| required | exception_type not null | exceptions | 190 | 0 | 0 | PASS |  |
| enum | exception_type in allowed values | exceptions | 190 | 0 | 0 | PASS |  |
| required | severity not null | exceptions | 190 | 0 | 0 | PASS |  |
| enum | severity in allowed values | exceptions | 190 | 0 | 0 | PASS |  |
| required | owner_role not null | exceptions | 190 | 0 | 0 | PASS |  |
| enum | owner_role in allowed values | exceptions | 190 | 0 | 0 | PASS |  |
| required | entity_type not null | exceptions | 190 | 0 | 0 | PASS |  |
| enum | entity_type in allowed values | exceptions | 190 | 0 | 0 | PASS |  |
| required | entity_id not null | exceptions | 190 | 0 | 0 | PASS |  |
| enum | currency in allowed values | exceptions | 190 | 0 | 0 | PASS |  |
| required | rule_id not null | exceptions | 190 | 0 | 0 | PASS |  |
| required | description not null | exceptions | 190 | 0 | 0 | PASS |  |
| required | detected_at not null | exceptions | 190 | 0 | 0 | PASS |  |
| required | status not null | exceptions | 190 | 0 | 0 | PASS |  |
| enum | status in allowed values | exceptions | 190 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (history_id) | exception_status_history | 386 | 0 | 0 | PASS |  |
| required | history_id not null | exception_status_history | 386 | 0 | 0 | PASS |  |
| id_format | history_id matches ^EXH-2026-\d{6}$ | exception_status_history | 386 | 0 | 0 | PASS |  |
| required | exception_id not null | exception_status_history | 386 | 0 | 0 | PASS |  |
| required | to_status not null | exception_status_history | 386 | 0 | 0 | PASS |  |
| enum | to_status in allowed values | exception_status_history | 386 | 0 | 0 | PASS |  |
| required | changed_at not null | exception_status_history | 386 | 0 | 0 | PASS |  |
| required | actor_role not null | exception_status_history | 386 | 0 | 0 | PASS |  |
| enum | actor_role in allowed values | exception_status_history | 386 | 0 | 0 | PASS |  |
| primary_key | unique, non-null (resolution_id) | resolutions | 183 | 0 | 0 | PASS |  |
| required | resolution_id not null | resolutions | 183 | 0 | 0 | PASS |  |
| id_format | resolution_id matches ^RES-2026-\d{6}$ | resolutions | 183 | 0 | 0 | PASS |  |
| required | exception_id not null | resolutions | 183 | 0 | 0 | PASS |  |
| unique | exception_id unique | resolutions | 183 | 0 | 0 | PASS |  |
| required | resolution_type not null | resolutions | 183 | 0 | 0 | PASS |  |
| required | resolved_by_role not null | resolutions | 183 | 0 | 0 | PASS |  |
| enum | resolved_by_role in allowed values | resolutions | 183 | 0 | 0 | PASS |  |
| required | resolved_at not null | resolutions | 183 | 0 | 0 | PASS |  |
| required | adjustment_amount_minor not null | resolutions | 183 | 0 | 0 | PASS |  |
| enum | currency in allowed values | resolutions | 183 | 0 | 0 | PASS |  |
| required | notes not null | resolutions | 183 | 0 | 0 | PASS |  |
| foreign_key | merchant_id -> merchants.merchant_id | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| foreign_key | merchant_id -> merchants.merchant_id | payment_orders | 5000 | 0 | 0 | PASS |  |
| foreign_key | payment_id -> payment_orders.payment_id | order_status_history | 15066 | 0 | 0 | PASS |  |
| foreign_key | cause_event_id -> processor_events.event_id | order_status_history | 10066 | 0 | 0 | PASS |  |
| foreign_key | payment_id -> payment_orders.payment_id | payment_attempts | 5500 | 0 | 0 | PASS |  |
| foreign_key | payment_id -> payment_orders.payment_id | processor_events | 10566 | 0 | 0 | PASS |  |
| foreign_key | attempt_id -> payment_attempts.attempt_id | processor_events | 10566 | 0 | 0 | PASS |  |
| foreign_key | event_id -> processor_events.event_id | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| foreign_key | payment_id -> payment_orders.payment_id | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| foreign_key | attempt_id -> payment_attempts.attempt_id | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| foreign_key | batch_id -> settlement_batches.batch_id | settlement_lines | 4298 | 0 | 0 | PASS |  |
| foreign_key | event_id -> processor_events.event_id | settlement_lines | 4298 | 0 | 0 | PASS |  |
| foreign_key | payment_id -> payment_orders.payment_id | settlement_lines | 4298 | 0 | 0 | PASS |  |
| foreign_key | merchant_id -> merchants.merchant_id | settlement_lines | 4298 | 0 | 0 | PASS |  |
| foreign_key | event_id -> processor_events.event_id | canonical_events | 10566 | 0 | 0 | PASS |  |
| foreign_key | payment_id -> payment_orders.payment_id | canonical_events | 10566 | 0 | 0 | PASS |  |
| foreign_key | attempt_id -> payment_attempts.attempt_id | canonical_events | 10566 | 0 | 0 | PASS |  |
| foreign_key | first_delivery_id -> webhook_deliveries.delivery_id | canonical_events | 10566 | 0 | 0 | PASS |  |
| foreign_key | match_id -> reconciliation_matches.match_id | match_items | 8790 | 0 | 0 | PASS |  |
| foreign_key | exception_id -> exceptions.exception_id | exception_status_history | 386 | 0 | 0 | PASS |  |
| foreign_key | exception_id -> exceptions.exception_id | resolutions | 183 | 0 | 0 | PASS |  |
| foreign_key | polymorphic entity_id exists | exceptions | 190 | 0 | 0 | PASS |  |
| foreign_key | polymorphic entity_id exists | match_items | 8790 | 0 | 0 | PASS |  |
| foreign_key | polymorphic entity_id exists | item_status | 10054 | 0 | 0 | PASS |  |
| date_ordering | attempt.created_at >= order.created_at | payment_attempts | 5500 | 0 | 0 | PASS |  |
| date_ordering | event.occurred_at >= attempt.created_at | processor_events | 10566 | 0 | 3 | PASS |  |
| date_ordering | refund.occurred_at >= capture.occurred_at | processor_events | 250 | 0 | 3 | PASS |  |
| date_ordering | delivery.received_at >= occurred_at | webhook_deliveries | 10738 | 0 | 0 | PASS |  |
| date_ordering | booking_date >= value_date | bank_statement_lines | 500 | 0 | 0 | PASS |  |
| date_ordering | effective_to null or >= effective_from | merchants | 200 | 0 | 0 | PASS |  |
| arithmetic | line net = gross - fee (capture) / -gross (refund) | settlement_lines | 4298 | 0 | 0 | PASS |  |
| arithmetic | line fee = fee schedule in force on capture date (refund fee 0) | settlement_lines | 4298 | 0 | 0 | PASS |  |
| effective_dating | fee versions contiguous (to + 1 day = next from) | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| effective_dating | effective_to null or >= effective_from | merchant_fee_schedules | 221 | 0 | 0 | PASS |  |
| effective_dating | exactly one current fee version per merchant | merchant_fee_schedules | 200 | 0 | 0 | PASS |  |
| effective_dating | v1 starts at merchant onboarding | merchant_fee_schedules | 200 | 0 | 0 | PASS |  |
| arithmetic | batch totals = sum of lines; net = cap - ref - fee | settlement_batches | 100 | 0 | 0 | PASS |  |
| arithmetic | order captured/refunded = sum of events | payment_orders | 5000 | 0 | 0 | PASS |  |
| arithmetic | refunded <= captured | payment_orders | 5000 | 0 | 0 | PASS |  |
| consistency | order currency = merchant currency | payment_orders | 5000 | 0 | 0 | PASS |  |
| lifecycle | order transitions allowed | order_status_history | 15066 | 0 | 0 | PASS |  |
| lifecycle | history from_status = previous to_status | order_status_history | 15066 | 0 | 0 | PASS |  |
| lifecycle | order.status = last history row | payment_orders | 5000 | 0 | 0 | PASS |  |
| lifecycle | failed attempt has failure_code | payment_attempts | 5500 | 0 | 0 | PASS |  |
| duplicates | duplicate webhook deliveries are labelled | webhook_deliveries | 10738 | 0 | 172 | PASS |  |
| duplicates | duplicate settlement lines are labelled | settlement_lines | 4298 | 0 | 3 | PASS |  |
| consistency | bank line currency = account currency | bank_statement_lines | 500 | 0 | 3 | PASS |  |
| volume | row count = target 200 | merchants | 1 | 0 | 0 | PASS | actual 200 |
| volume | row count = target 5000 | payment_orders | 1 | 0 | 0 | PASS | actual 5000 |
| volume | row count = target 5500 | payment_attempts | 1 | 0 | 0 | PASS | actual 5500 |
| volume | row count = target 100 | settlement_batches | 1 | 0 | 0 | PASS | actual 100 |
| volume | row count = target 500 | bank_statement_lines | 1 | 0 | 0 | PASS | actual 500 |
| acceptance | matched amounts within tolerance (1 minor) | reconciliation_matches | 4389 | 0 | 0 | PASS |  |
| acceptance | every item matched, explained or an exception | item_status | 10054 | 0 | 0 | PASS |  |
| acceptance | every partial match has an exception | reconciliation_matches | 3 | 0 | 0 | PASS |  |
| acceptance | every settlement line is matched or an exception | settlement_lines | 4298 | 0 | 0 | PASS |  |
| acceptance | dedup is idempotent: canonical events = registry | canonical_events | 10566 | 0 | 0 | PASS |  |
| acceptance | fee/refund treatment consistent (no fee-rule exceptions) | exceptions | 190 | 0 | 0 | PASS |  |
| lifecycle | exception.status = latest history row | exceptions | 190 | 0 | 0 | PASS |  |
| lifecycle | resolved exceptions have exactly one resolution | resolutions | 183 | 0 | 0 | PASS |  |
