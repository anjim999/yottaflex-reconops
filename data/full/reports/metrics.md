# Evaluation metrics

Engine decisions scored against `ground_truth/ground_truth.csv` (the engine never reads it).

## Anomaly detection (per exception type)

| exception_type | expected | detected | true_positive | false_positive | false_negative | precision | recall | f1 |
|---|---|---|---|---|---|---|---|---|
| CURRENCY_MISMATCH | 15 | 15 | 15 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| DUPLICATE_SETTLEMENT_LINE | 30 | 30 | 30 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| DUPLICATE_WEBHOOK | 1791 | 1791 | 1791 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| FEE_DIFFERENCE | 20 | 20 | 20 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| MISSING_SETTLEMENT_LINE | 30 | 30 | 30 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| REFUND_BEFORE_CAPTURE | 30 | 30 | 30 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| UNMATCHED_BANK_LINE | 10 | 10 | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| ALL (micro) | 1926 | 1926 | 1926 | 0 | 0 | 1.0 | 1.0 | 1.0 |

## Expected decisions on labelled normal cases

| issue_type | expected_decision | cases | correct | accuracy |
|---|---|---|---|---|
| DELAYED_SETTLEMENT | MATCHED | 2006 | 2006 | 1.0 |
| MISSING_BANK_REFERENCE | MATCHED_FUZZY | 35 | 35 | 1.0 |
| ROUNDING_DIFFERENCE | MATCHED_WITHIN_TOLERANCE | 24 | 24 | 1.0 |
| SPLIT_PAYOUT | MATCHED_SPLIT | 60 | 60 | 1.0 |

## Idempotency

- **same_input_twice_identical_output**: True
- **replayed_full_webhook_feed_canonical_events_unchanged**: True
- **replayed_feed_matches_unchanged**: True
- **replayed_feed_non_duplicate_exceptions_unchanged**: True
- **replayed_feed_extra_duplicates_flagged**: 109237

## Reconciliation KPIs

```json
{
  "event_settlement_match_rate": 0.9994,
  "settlement_line_match_rate": 0.9994,
  "batch_bank_match_rate": 0.965,
  "processor_bank_line_match_rate": 0.9579,
  "status_breakdown": {
    "PROCESSOR_EVENT": {
      "MATCHED": 50707,
      "OUT_OF_PERIOD": 544,
      "IN_TRANSIT": 168,
      "EXCEPTION": 30
    },
    "SETTLEMENT_LINE": {
      "MATCHED": 50707,
      "EXCEPTION": 30
    },
    "SETTLEMENT_BATCH": {
      "MATCHED": 965,
      "EXCEPTION": 35
    },
    "BANK_LINE": {
      "OUT_OF_SCOPE": 3930,
      "MATCHED": 1025,
      "EXCEPTION": 25,
      "PARTIAL": 20
    }
  },
  "settled_net_usd_equiv": 2802584.26,
  "matched_net_usd_equiv": 2692699.54,
  "amount_match_rate": 0.9608,
  "exceptions_total": 1926,
  "exceptions_by_type": {
    "DUPLICATE_WEBHOOK": 1791,
    "REFUND_BEFORE_CAPTURE": 30,
    "DUPLICATE_SETTLEMENT_LINE": 30,
    "MISSING_SETTLEMENT_LINE": 30,
    "FEE_DIFFERENCE": 20,
    "CURRENCY_MISMATCH": 15,
    "UNMATCHED_BANK_LINE": 10
  },
  "exceptions_by_severity": {
    "LOW": 1791,
    "HIGH": 90,
    "MEDIUM": 30,
    "CRITICAL": 15
  },
  "exceptions_by_status": {
    "RESOLVED": 1871,
    "OPEN": 30,
    "ESCALATED": 25
  },
  "resolution_rate": 0.9714,
  "open_exception_amount_usd_equiv": 34968.25
}
```
