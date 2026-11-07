# Data profile

Distributions of the generated data (evidence for realistic, varied data).

## Order amount by currency major units

| currency | min | p05 | p50 | mean | p95 | max |
|---|---|---|---|---|---|---|
| EUR | 1.3 | 8.34 | 39.23 | 60.04 | 180.15 | 1680.82 |
| GBP | 0.79 | 6.85 | 33.61 | 52.9 | 160.21 | 1543.69 |
| INR | 163.6 | 752.35 | 3422.9 | 5487.08 | 16517.57 | 128514.48 |
| JPY | 154.0 | 1350.75 | 6160.0 | 9787.21 | 30234.25 | 287860.0 |
| USD | 1.0 | 8.54 | 42.66 | 67.03 | 204.59 | 2093.05 |

## Merchant concentration

| merchants_with_orders | orders_top_1pct_merchants_share | orders_top_10pct_merchants_share | median_orders_per_merchant | max_orders_per_merchant |
|---|---|---|---|---|
| 1990 | 0.352 | 0.629 | 9 | 4998 |

## Currency mix

| currency | share |
|---|---|
| USD | 0.403 |
| EUR | 0.247 |
| GBP | 0.149 |
| INR | 0.118 |
| JPY | 0.082 |

## Payment method mix

| payment_method | share |
|---|---|
| CARD | 0.719 |
| WALLET | 0.198 |
| BANK_TRANSFER | 0.082 |

## Order status mix

| status | share |
|---|---|
| CAPTURED | 0.8509 |
| PARTIALLY_REFUNDED | 0.062 |
| FAILED | 0.0401 |
| REFUNDED | 0.0271 |
| VOIDED | 0.0199 |

## Attempts per order

| attempts | orders |
|---|---|
| 1 | 45000 |
| 2 | 5000 |

## Failure codes

| failure_code | attempts |
|---|---|
| insufficient_funds | 1198 |
| authentication_failed | 1190 |
| card_declined | 1180 |
| expired_card | 1164 |
| do_not_honor | 1143 |
| processing_error | 1131 |

## Event type mix

| event_type | events |
|---|---|
| payment.authorized | 47994 |
| payment.captured | 46997 |
| payment.failed | 7006 |
| payment.refunded | 4452 |
| payment.voided | 997 |

## Refunds

| refund_rate_of_captures | partial_refund_share | median_partial_refund_ratio |
|---|---|---|
| 0.0947 | 0.696 | 0.502 |

## Capture to settlement days

| days | lines |
|---|---|
| 1 | 24720 |
| 2 | 19034 |
| 3 | 5866 |
| 4 | 715 |
| 5 | 306 |
| 6 | 67 |
| 7 | 2 |
| 8 | 4 |
| 10 | 2 |
| 11 | 1 |
| 12 | 1 |
| 14 | 2 |
| 15 | 2 |
| 16 | 3 |
| 17 | 3 |
| 18 | 1 |
| 19 | 1 |
| 20 | 2 |
| 21 | 3 |
| 22 | 1 |
| 23 | 1 |

## Fees

| effective_fee_rate_pct | merchants_repriced_mid_period | risk_tier_mix |
|---|---|---|
| 1.99 | 193 | {'LOW': 1211, 'MEDIUM': 592, 'HIGH': 197} |

## Lines per batch

| min | p05 | p50 | mean | p95 | max |
|---|---|---|---|---|---|
| 10 | 18.0 | 38.5 | 50.7 | 112.0 | 130 |

## Bank lines by type

| transaction_code | direction | lines |
|---|---|---|
| BANK_CHARGE | DEBIT | 777 |
| CREDIT_TRANSFER | CREDIT | 2057 |
| DEBIT_TRANSFER | DEBIT | 1757 |
| INTEREST | CREDIT | 409 |
