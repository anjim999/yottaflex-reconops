# Data profile

Distributions of the generated data (evidence for realistic, varied data).

## Order amount by currency major units

| currency | min | p05 | p50 | mean | p95 | max |
|---|---|---|---|---|---|---|
| EUR | 1.29 | 7.66 | 38.34 | 63.27 | 200.46 | 839.54 |
| GBP | 1.13 | 6.62 | 31.8 | 47.81 | 141.34 | 556.39 |
| INR | 198.27 | 772.9 | 3217.83 | 5058.68 | 14878.3 | 56344.51 |
| JPY | 402.0 | 1527.55 | 6157.0 | 9730.12 | 26986.15 | 205598.0 |
| USD | 2.72 | 9.26 | 42.06 | 66.41 | 196.57 | 2040.79 |

## Merchant concentration

| merchants_with_orders | orders_top_1pct_merchants_share | orders_top_10pct_merchants_share | median_orders_per_merchant | max_orders_per_merchant |
|---|---|---|---|---|
| 200 | 0.117 | 0.464 | 14 | 360 |

## Currency mix

| currency | share |
|---|---|
| USD | 0.39 |
| EUR | 0.246 |
| GBP | 0.153 |
| INR | 0.125 |
| JPY | 0.086 |

## Payment method mix

| payment_method | share |
|---|---|
| CARD | 0.722 |
| WALLET | 0.198 |
| BANK_TRANSFER | 0.08 |

## Order status mix

| status | share |
|---|---|
| CAPTURED | 0.8962 |
| FAILED | 0.0368 |
| PARTIALLY_REFUNDED | 0.033 |
| VOIDED | 0.017 |
| REFUNDED | 0.017 |

## Attempts per order

| attempts | orders |
|---|---|
| 1 | 4500 |
| 2 | 500 |

## Failure codes

| failure_code | attempts |
|---|---|
| expired_card | 122 |
| do_not_honor | 121 |
| card_declined | 116 |
| insufficient_funds | 112 |
| processing_error | 110 |
| authentication_failed | 103 |

## Event type mix

| event_type | events |
|---|---|
| payment.authorized | 4816 |
| payment.captured | 4731 |
| payment.failed | 684 |
| payment.refunded | 250 |
| payment.voided | 85 |

## Refunds

| refund_rate_of_captures | partial_refund_share | median_partial_refund_ratio |
|---|---|---|
| 0.0528 | 0.66 | 0.5 |

## Capture to settlement days

| days | lines |
|---|---|
| 1 | 1889 |
| 2 | 1640 |
| 3 | 665 |
| 4 | 69 |
| 5 | 23 |
| 6 | 10 |
| 13 | 1 |
| 18 | 1 |

## Fees

| effective_fee_rate_pct | merchants_repriced_mid_period | risk_tier_mix |
|---|---|---|
| 1.997 | 21 | {'LOW': 123, 'MEDIUM': 59, 'HIGH': 18} |

## Lines per batch

| min | p05 | p50 | mean | p95 | max |
|---|---|---|---|---|---|
| 13 | 16.0 | 34.0 | 43.0 | 88.0 | 112 |

## Bank lines by type

| transaction_code | direction | lines |
|---|---|---|
| BANK_CHARGE | DEBIT | 75 |
| CREDIT_TRANSFER | CREDIT | 211 |
| DEBIT_TRANSFER | DEBIT | 175 |
| INTEREST | CREDIT | 39 |
