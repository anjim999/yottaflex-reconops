"""Reconciliation engine entry point. Reads only input tables + run config, never ground truth."""
import pandas as pd

from ..config import Period, Rules
from .ingest import ingest_deliveries
from .ledger import Ledger
from .lifecycle import check_lifecycle
from .match_bank import match_batches_to_bank
from .match_lines import match_events_to_lines
from .resolve import apply_workflow

ENGINE_INPUTS = ["merchants", "merchant_fee_schedules", "payment_orders", "payment_attempts", "webhook_deliveries",
                 "settlement_batches", "settlement_lines", "bank_statement_lines"]


def _prep(t: dict) -> dict:
    t = {k: t[k].copy() for k in ENGINE_INPUTS}
    for col in ("occurred_at", "received_at"):
        t["webhook_deliveries"][col] = pd.to_datetime(t["webhook_deliveries"][col], utc=True)
    t["settlement_batches"]["settlement_date"] = pd.to_datetime(t["settlement_batches"]["settlement_date"]).dt.date
    t["bank_statement_lines"]["value_date"] = pd.to_datetime(t["bank_statement_lines"]["value_date"]).dt.date
    t["merchant_fee_schedules"]["effective_from"] = pd.to_datetime(t["merchant_fee_schedules"]["effective_from"]).dt.date
    return t


def reconcile(tables: dict, run_config: dict) -> dict:
    t = _prep(tables)
    rules = Rules(**run_config["rules"])
    period = Period.from_dict(run_config["period"])
    ledger = Ledger(period.run_at.strftime("%Y-%m-%dT%H:%M:%SZ"))

    events = ingest_deliveries(t["webhook_deliveries"], ledger)
    check_lifecycle(events, t["payment_orders"], t["payment_attempts"], ledger)
    match_events_to_lines(events, t["settlement_lines"], t["settlement_batches"], t["payment_orders"],
                          t["merchants"], t["merchant_fee_schedules"], rules, period, ledger)
    match_batches_to_bank(t["settlement_batches"], t["bank_statement_lines"], rules, period, ledger)

    exceptions, history, resolutions = apply_workflow(pd.DataFrame(ledger.exceptions), period.run_at, run_config["seed"])
    item_status = pd.DataFrame([{"item_type": k[0], "item_id": k[1], "recon_status": v[0], "reason": v[1]}
                                for k, v in sorted(ledger.status.items())])
    canonical = events.copy()
    for col in ("occurred_at", "first_received_at"):
        canonical[col] = canonical[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "canonical_events": canonical,
        "reconciliation_matches": pd.DataFrame(ledger.matches),
        "match_items": pd.DataFrame(ledger.items),
        "exceptions": exceptions,
        "exception_status_history": history,
        "resolutions": resolutions,
        "item_status": item_status,
    }
