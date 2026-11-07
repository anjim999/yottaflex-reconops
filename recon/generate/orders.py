"""Step 2: PaymentOrders, linked to valid merchants, chronological IDs."""
from datetime import datetime, time, timedelta

import numpy as np
import pandas as pd

from ..config import CURRENCIES, CURRENCY_CODES, START_DATE, UTC, WARMUP_DAYS
from ..ids import customer_ref, payment_id


def generate_orders(scale, merchants: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng([seed, 2])
    n = scale.orders
    dates = [START_DATE + timedelta(days=d) for d in range(-WARMUP_DAYS, scale.settlement_days)]
    day_w = np.array([1.0 if d.weekday() < 5 else 0.75 for d in dates])  # weekend dip
    day_idx = rng.choice(len(dates), size=n, p=day_w / day_w.sum())
    secs = rng.integers(0, 86_400, size=n)

    shares = np.array([c.volume_share for c in CURRENCIES.values()])
    ccy = rng.choice(CURRENCY_CODES, size=n, p=shares)
    merchant_of = np.empty(n, dtype=object)
    weight = rng.pareto(1.16, len(merchants)) + 1.0  # few large merchants, long tail
    m_ccy = merchants["settlement_currency"].to_numpy()
    m_ids = merchants["merchant_id"].to_numpy()
    for code in CURRENCY_CODES:
        pool = np.flatnonzero(m_ccy == code)
        sel = np.flatnonzero(ccy == code)
        p = weight[pool] / weight[pool].sum()
        merchant_of[sel] = m_ids[rng.choice(pool, size=len(sel), p=p)]

    usd = rng.lognormal(np.log(42), 0.95, size=n)  # basket size in USD-equivalent
    method = rng.choice(["CARD", "WALLET", "BANK_TRANSFER"], size=n, p=[0.72, 0.20, 0.08])
    cust = rng.integers(1, max(2, n // 3) + 1, size=n)

    rows = []
    for k, i in enumerate(np.lexsort((secs, day_idx)), start=1):
        cur = CURRENCIES[str(ccy[i])]
        major = max(usd[i], 1.0) * cur.fx_per_usd
        rows.append({
            "payment_id": payment_id(k),
            "merchant_id": merchant_of[i],
            "customer_ref": customer_ref(int(cust[i])),
            "amount_minor": int(round(major * 10 ** cur.exponent)),
            "currency": cur.code,
            "payment_method": str(method[i]),
            "created_at": datetime.combine(dates[day_idx[i]], time(0), tzinfo=UTC) + timedelta(seconds=int(secs[i])),
        })
    return pd.DataFrame(rows)
