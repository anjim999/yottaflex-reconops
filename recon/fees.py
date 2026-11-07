"""Effective-dated merchant fee terms: the fee in force on the event date is the one applied."""
from bisect import bisect_right
from collections import defaultdict
from datetime import date

import pandas as pd

from .money import fee_minor


class FeeBook:
    def __init__(self, schedules: pd.DataFrame):
        self._by_merchant = defaultdict(list)
        for s in schedules.sort_values(["merchant_id", "effective_from"]).itertuples(index=False):
            start = s.effective_from if isinstance(s.effective_from, date) else date.fromisoformat(str(s.effective_from))
            self._by_merchant[s.merchant_id].append((start, s.fee_schedule_id, int(s.fee_rate_bps), int(s.fixed_fee_minor)))
        self._starts = {m: [v[0] for v in vs] for m, vs in self._by_merchant.items()}

    def terms(self, merchant_id: str, on: date):
        """(fee_schedule_id, bps, fixed) effective on `on`; earliest schedule if `on` precedes all."""
        versions = self._by_merchant[merchant_id]
        i = max(bisect_right(self._starts[merchant_id], on) - 1, 0)
        return versions[i][1:]

    def fee(self, merchant_id: str, on: date, gross_minor: int) -> int:
        _, bps, fixed = self.terms(merchant_id, on)
        return fee_minor(gross_minor, bps, fixed)
