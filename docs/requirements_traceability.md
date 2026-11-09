# Requirements traceability

Each line of the problem statement, with where it is implemented and how it is proven.
Evidence paths are relative to the repository root. Reports are under `data/<scale>/reports/`.

## Objective and scope

| Requirement | Implementation | Evidence |
|---|---|---|
| Working end-to-end reconciliation workflow | `python -m recon all` runs generate → reconcile → validate → evaluate → SQL → DB → reproduce | README Quick start; `tests/test_engine.py` |
| Expose key decisions and exceptions | Each match carries `match_type` and `rule_id`. Each exception carries `rule_id`, severity, owner and trace ids. `item_status` gives every record exactly one decision. The web console shows all of it. | `output/reconciliation_matches.csv`, `output/exceptions.csv`, `output/item_status.csv`; web app pages |
| Preserve traceability | `match_items` bridge, `related_ids` on exceptions, `cause_event_id` on order history, trace API / Trace explorer | `GET /api/trace/{id}`; `test_traceability_every_exception_points_at_a_real_record` |
| Produce measurable outputs | Precision / recall / F1 per exception type, decision accuracy on normal cases, match rates, amount match rate, exposure | `reports/metrics.md`, `reports/metrics.json` |
| Medium complexity: multiple entities, conditional rules, exception path, metrics | 10 required entities plus history, bridge and fee-schedule tables; 19 exception types; tolerance, date-window, grace and fuzzy rules | `recon/engine/catalog.py`, `docs/erd.md` |

## Primary actors

| Actor | Where |
|---|---|
| Customer / account holder | Web → Payment lookup (timeline per payment), `GET /api/payments/{id}` |
| Operations analyst | Web → Exception queue: start review, resolve, escalate. Append-only history. |
| Risk / compliance reviewer | Web → Risk & compliance: risk-owned queue, audit trail, adjustments. Segregation of duties (`403`). |
| System administrator | Web → System admin: run config, 274 validation checks, reproducibility, idempotency, manifest |

## Business workflow and rules

| # | Requirement | Implementation | Evidence |
|---|---|---|---|
| 1 | Master data first: Merchant, PaymentOrder, PaymentAttempt, ProcessorEvent, SettlementBatch | `generate/pipeline.py` order: merchants (+ fee schedules) → orders → attempts/events → settlement | `pipeline.py` |
| 2 | Dependent records use valid parent IDs | Children are built only from parent rows | Validation `foreign_key` checks (0 failures); `test_foreign_keys`; SQL FK constraints; SQLite `foreign_key_check` |
| 3 | Merchants/orders → attempts/events → batches with fees → bank lines → match by reference, amount, currency, date window → exceptions → resolutions | `generate/*`, `engine/match_lines.py`, `engine/match_bank.py`, `engine/resolve.py` | `tests/test_rules.py` (exact, tolerance, fee, currency, window, fuzzy) |
| 4 | Persist state changes as records; never overwrite history | `order_status_history`, `exception_status_history`, `resolutions`. Status is derived from the latest row. API actions only INSERT. | `test_exception_history_append_only_and_status_derived`, `test_workflow_appends_history_and_resolution` |
| 5 | Outcomes and labels from documented rules | Each injector in `generate/anomalies.py` emits its own label. Order status is derived from events. | `ground_truth/ground_truth.csv` (`injection_rule` column) |

## Entities and relationships

| Requirement | Evidence |
|---|---|
| PK for every entity, FK for every relationship | `recon/schema.py` → `sql/schema.sql` (PRIMARY KEY, FOREIGN KEY, CHECK); validation `primary_key` / `foreign_key` |
| Cardinality, optional relationships | `docs/erd.md` (Mermaid ERD and cardinality table) |
| Effective dates | `merchant_fee_schedules` (SCD-2): about 10% of merchants are repriced mid-period, and the fee in force on the capture date is applied. Checks: contiguity, one current version, v1 = onboarding. | `test_effective_dated_fees_applied_by_capture_date`; validation `effective_dating` |
| Lifecycle states | Order and exception state machines (`generate/status.py`, `engine/resolve.py`) | Validation `lifecycle`; API returns `409` on an illegal transition |
| Bridge tables for N:M | `match_items` (batch ↔ bank lines; split payouts are 1:2) | `SPLIT_PAYOUT` decision accuracy 100% |
| Retain event history | `webhook_deliveries` keeps every raw delivery; `processor_events` registry; status-history tables | `canonical_events` vs registry check |
| Validate all joins | 30+ FK checks, including polymorphic `entity_id` | `reports/validation_summary.md` |
| Anomalies labelled, not silently corrupting unrelated rows | `ground_truth.csv` with `issue_type`. Injectors touch only target rows. Totals are recomputed. | Validation counts "labelled" separately; unlabelled violations = 0 |

## ID conventions

| Format | Check |
|---|---|
| `PAY-2026-00000001`, `ATT-<payment-id>-01`, `SET-2026-000001`, `STL-<batch-id>-001`, `BANK-2026-000001`, `REC-2026-000001` | `test_id_formats_match_brief`; regex validation on every ID column; IDs assigned chronologically, never renumbered, and API actions continue the counters |

## Synthetic data generation steps

| Step | Evidence |
|---|---|
| 1. Data dictionary: type, required, allowed values, units, uniqueness, validation | `docs/data_dictionary.md` (generated from `recon/schema.py`) |
| 2. Parents before children; domain logic | `generate/pipeline.py` |
| 3. Deterministic IDs, consistent across files | `recon/ids.py`; FK validation across all CSVs |
| 4. Volumes 2,000 / 50,000 / 55,000 / 1,000 / 5,000; delayed settlements, fees, partial refunds, duplicate webhooks, currency rounding; fixed seed; parameterised scale | `--scale starter\|full --seed 20261022`; validation `volume`; `reports/data_profile.md` |
| 5. Baseline first, then labelled edge cases (all 6) | `generate/anomalies.py`, `generate/deliveries.py`; `test_all_required_edge_cases_labelled` |
| 6. Derived values computed from source records | Order status and amounts from events; batch totals from lines; payout from net; validation `arithmetic` |
| 7. Separate ground truth, never leaked | `ground_truth/` only; the engine reads `ENGINE_INPUTS` only; `test_ground_truth_not_leaked_into_inputs` |
| 8. Validation: PK, FK, enums, date ordering, arithmetic, lifecycle, duplicates | `recon/validate.py` → 274 checks, 0 failures |
| 9. CSV / JSON / SQL seed, README, schema, generator command, seed, manifest, validation summary | `input/*.csv`, `input/json/`, `sql/schema.sql`, `sql/seed.sql`, `manifest.json` (command, seed, versions, SHA-256), `reports/validation_summary.md` |
| 10. Regenerate twice and compare counts/checksums | `python -m recon reproduce` → `reports/reproducibility_report.json` (`identical: true`); `test_same_seed_is_reproducible` |

## Required edge cases

| Edge case | Expected exception | Result (full scale) |
|---|---|---|
| Duplicate settlement line | `DUPLICATE_SETTLEMENT_LINE` | 30 / 30, 0 FP |
| Bank amount differs by fee | `FEE_DIFFERENCE` (partial match) | 20 / 20, 0 FP |
| Refund appears before capture | `REFUND_BEFORE_CAPTURE` | 30 / 30, 0 FP |
| Unmatched record silently dropped | `MISSING_SETTLEMENT_LINE`, `UNMATCHED_BANK_LINE` | 30 / 30 and 10 / 10, 0 FP |
| Currency mismatch | `CURRENCY_MISMATCH` (never auto-matched) | 15 / 15, 0 FP |
| Same processor event ingested twice | `DUPLICATE_WEBHOOK` + idempotent dedupe | 1,791 / 1,791, 0 FP |

## Acceptance criteria

| Criterion | Evidence |
|---|---|
| Matched amounts reconcile under configured tolerance | Validation: 0 MATCHED rows with \|diff\| > tolerance; `test_matched_amounts_within_tolerance` |
| Every unmatched item is an exception | `item_status` coverage; every PARTIAL match has an exception; every settlement line is matched or an exception; `test_every_unmatched_item_is_an_exception` |
| Duplicate events are idempotent | Full webhook feed replayed: canonical events and matches unchanged; `test_duplicate_events_are_idempotent` |
| Fee and refund treatment consistent | Every line fee recomputed from the effective-dated schedule (0 violations); refund fee = 0; `test_fee_and_refund_treatment_consistent` |

## Evaluation focus

| Focus | Evidence |
|---|---|
| (a) Realistic distributions, meaningful variation | `reports/data_profile.md` (amount quantiles per currency, merchant concentration, retries, failure codes, refund mix, settlement lag, fees, bank activity mix) |
| (b) Consistent IDs, valid joins | Regex and FK validation; SQL constraints |
| (c) Dependency / lifecycle consistency | `lifecycle` and `date_ordering` validation |
| (d) Correct derived values and reconciliation | `arithmetic` validation; precision/recall 1.0 |
| (e) Normal, boundary, failure, exception coverage | Normal-case labels (delayed, rounding at the tolerance boundary, split, fuzzy), failed attempts, voids, 6 anomaly types; `test_rules.py` boundary tests (tolerance ±1 vs ±2, date window) |
| (f) Separate ground truth | `ground_truth/ground_truth.{csv,json}` |
| (g) Fixed-seed reproducibility, documentation, lawful provenance | `reproducibility_report.json`; README; `manifest.json` provenance: 100% synthetic, no external data |

## Submission checklist

- [x] README explains how to run it
- [x] Tests: `pytest` (40 tests: generator, engine, rules, API, committed-data checksums)
- [x] Public GitHub repository: https://github.com/anjim999/yottaflex-reconops
