# Evaluation metrics

Engine decisions scored against `ground_truth/ground_truth.csv` (the engine never reads it).

## Anomaly detection (per exception type)

| exception_type | expected | detected | true_positive | false_positive | false_negative | precision | recall | f1 |
|---|---|---|---|---|---|---|---|---|
| CURRENCY_MISMATCH | 3 | 3 | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| DUPLICATE_SETTLEMENT_LINE | 3 | 3 | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| DUPLICATE_WEBHOOK | 172 | 172 | 172 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| FEE_DIFFERENCE | 3 | 3 | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| MISSING_SETTLEMENT_LINE | 3 | 3 | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| REFUND_BEFORE_CAPTURE | 3 | 3 | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| UNMATCHED_BANK_LINE | 3 | 3 | 3 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| ALL (micro) | 190 | 190 | 190 | 0 | 0 | 1.0 | 1.0 | 1.0 |

## Expected decisions on labelled normal cases

| issue_type | expected_decision | cases | correct | accuracy |
|---|---|---|---|---|
| DELAYED_SETTLEMENT | MATCHED | 188 | 188 | 1.0 |
| MISSING_BANK_REFERENCE | MATCHED_FUZZY | 3 | 3 | 1.0 |
| ROUNDING_DIFFERENCE | MATCHED_WITHIN_TOLERANCE | 3 | 3 | 1.0 |
| SPLIT_PAYOUT | MATCHED_SPLIT | 6 | 6 | 1.0 |

## Idempotency

- **same_input_twice_identical_output**: True
- **replayed_full_webhook_feed_canonical_events_unchanged**: True
- **replayed_feed_matches_unchanged**: True
- **replayed_feed_non_duplicate_exceptions_unchanged**: True
- **replayed_feed_extra_duplicates_flagged**: 10738

## Reconciliation KPIs

```json
{
  "event_settlement_match_rate": 0.9993,
  "settlement_line_match_rate": 0.9993,
  "batch_bank_match_rate": 0.94,
  "processor_bank_line_match_rate": 0.9174,
  "status_breakdown": {
    "PROCESSOR_EVENT": {
      "MATCHED": 4295,
      "OUT_OF_PERIOD": 474,
      "IN_TRANSIT": 209,
      "EXCEPTION": 3
    },
    "SETTLEMENT_LINE": {
      "MATCHED": 4295,
      "EXCEPTION": 3
    },
    "SETTLEMENT_BATCH": {
      "MATCHED": 94,
      "EXCEPTION": 6
    },
    "BANK_LINE": {
      "OUT_OF_SCOPE": 391,
      "MATCHED": 100,
      "EXCEPTION": 6,
      "PARTIAL": 3
    }
  },
  "settled_net_usd_equiv": 246163.78,
  "matched_net_usd_equiv": 231836.39,
  "amount_match_rate": 0.9418,
  "exceptions_total": 190,
  "exceptions_by_type": {
    "DUPLICATE_WEBHOOK": 172,
    "REFUND_BEFORE_CAPTURE": 3,
    "DUPLICATE_SETTLEMENT_LINE": 3,
    "MISSING_SETTLEMENT_LINE": 3,
    "FEE_DIFFERENCE": 3,
    "CURRENCY_MISMATCH": 3,
    "UNMATCHED_BANK_LINE": 3
  },
  "exceptions_by_severity": {
    "LOW": 172,
    "HIGH": 9,
    "MEDIUM": 6,
    "CRITICAL": 3
  },
  "exceptions_by_status": {
    "RESOLVED": 183,
    "OPEN": 5,
    "ESCALATED": 2
  },
  "resolution_rate": 0.9632,
  "open_exception_amount_usd_equiv": 4420.99
}
```
