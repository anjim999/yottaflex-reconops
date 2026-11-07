"""Append-only record keeper for matches, exceptions and per-item reconciliation status."""
from ..ids import exception_id, match_id
from .catalog import EXCEPTIONS

STATUS_PRIORITY = {"OUT_OF_SCOPE": 0, "OUT_OF_PERIOD": 1, "IN_TRANSIT": 2, "MATCHED": 3, "PARTIAL": 4, "EXCEPTION": 5}


class Ledger:
    def __init__(self, decided_at: str, engine_version: str = "recon-engine/1.0"):
        self.decided_at, self.actor = decided_at, engine_version
        self.matches, self.items, self.exceptions = [], [], []
        self.status = {}  # (item_type, item_id) -> (status, reason)

    def match(self, level, match_type, status, rule_id, left, right, left_amt, right_amt, currency):
        mid = match_id(len(self.matches) + 1)
        self.matches.append({
            "match_id": mid, "match_level": level, "match_type": match_type, "status": status,
            "rule_id": rule_id, "left_amount_minor": int(left_amt), "right_amount_minor": int(right_amt),
            "difference_minor": int(right_amt - left_amt), "currency": currency,
            "decided_at": self.decided_at, "decided_by": self.actor,
        })
        for side, refs in (("LEFT", left), ("RIGHT", right)):
            for etype, eid in refs:
                self.items.append({"match_id": mid, "entity_type": etype, "entity_id": eid, "side": side})
        return mid

    def exception(self, etype, entity_type, entity_id, detail="", related=(), amount=None, currency=None):
        severity, owner, _, rule_id, desc = EXCEPTIONS[etype]
        xid = exception_id(len(self.exceptions) + 1)
        self.exceptions.append({
            "exception_id": xid, "exception_type": etype, "severity": severity, "owner_role": owner,
            "entity_type": entity_type, "entity_id": entity_id, "related_ids": "|".join(related),
            "amount_minor": None if amount is None else int(amount), "currency": currency, "rule_id": rule_id,
            "description": f"{desc} {detail}".strip(), "detected_at": self.decided_at,
        })
        self.set_status(entity_type, entity_id, "EXCEPTION", etype)
        return xid

    def set_status(self, item_type, item_id, status, reason):
        key = (item_type, item_id)
        cur = self.status.get(key)
        if cur is None or STATUS_PRIORITY[status] > STATUS_PRIORITY[cur[0]]:
            self.status[key] = (status, reason)
