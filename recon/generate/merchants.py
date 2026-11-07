"""Step 1 of generation: Merchant master data."""
from datetime import timedelta

import numpy as np
import pandas as pd

from ..config import CURRENCIES, CURRENCY_CODES, START_DATE
from ..ids import fee_schedule_id, merchant_id

ADJ = ["Blue", "Golden", "Silver", "Northern", "Urban", "Bright", "Green", "Swift", "Prime", "Coastal",
       "Royal", "Lunar", "Solar", "Maple", "Cedar", "Iron", "Crystal", "Summit", "River", "Harbor"]
NOUN = ["Bazaar", "Kitchen", "Outfitters", "Labs", "Studio", "Market", "Goods", "Supply", "Travel", "Books",
        "Pharmacy", "Electronics", "Apparel", "Coffee", "Fitness", "Games", "Florist", "Motors", "Bakery", "Home"]
SUFFIX = {"US": "LLC", "DE": "GmbH", "FR": "SARL", "ES": "SL", "IT": "SRL", "NL": "BV",
          "GB": "Ltd", "IN": "Pvt Ltd", "JP": "KK"}
MCC = ["5411", "5812", "5999", "7372", "4722", "5732", "5691", "5942"]
BPS_RANGE = {"LOW": (120, 201), "MEDIUM": (180, 261), "HIGH": (250, 351)}


def generate_merchants(scale, seed: int):
    """Returns (merchants, merchant_fee_schedules). ~10% of merchants are repriced mid-period."""
    rng = np.random.default_rng([seed, 1])
    n = scale.merchants
    shares = np.array([c.volume_share for c in CURRENCIES.values()])
    ccys = rng.choice(CURRENCY_CODES, size=n, p=shares).astype(object)
    ccys[: len(CURRENCY_CODES)] = CURRENCY_CODES  # every currency has at least one merchant
    tiers = rng.choice(["LOW", "MEDIUM", "HIGH"], size=n, p=[0.6, 0.3, 0.1])
    delays = rng.choice([1, 2, 3], size=n, p=[0.5, 0.35, 0.15])

    rows, terms = [], []
    for i in range(n):
        cur = CURRENCIES[str(ccys[i])]
        country = cur.countries[int(rng.integers(len(cur.countries)))]
        lo, hi = BPS_RANGE[str(tiers[i])]
        onboarded = START_DATE - timedelta(days=int(rng.integers(30, 1500)))
        rows.append({
            "merchant_id": merchant_id(i + 1),
            "legal_name": f"{rng.choice(ADJ)} {rng.choice(NOUN)} {SUFFIX[country]}",
            "country": country,
            "settlement_currency": cur.code,
            "mcc": str(rng.choice(MCC)),
            "risk_tier": str(tiers[i]),
            "settlement_delay_days": int(delays[i]),
            "status": "ACTIVE",
            "onboarded_on": onboarded,
            "effective_from": onboarded,
            "effective_to": None,
        })
        terms.append((int(rng.integers(lo, hi)), cur.fixed_fee_minor, onboarded))
    return pd.DataFrame(rows), fee_schedules(rows, terms, scale, seed)


def fee_schedules(merchants, terms, scale, seed):
    """Effective-dated fee terms. A repricing closes the old version the day before the new one starts."""
    rng = np.random.default_rng([seed, 8])
    out = []
    for m, (bps, fixed, start) in zip(merchants, terms):
        versions = [(bps, fixed, start)]
        buffer = max(3, scale.settlement_days // 6)  # reprice well inside the period
        if rng.random() < 0.10:
            change = START_DATE + timedelta(days=int(rng.integers(buffer, scale.settlement_days - buffer)))
            versions.append((int(np.clip(bps + rng.choice([-1, 1]) * rng.integers(10, 41), 100, 400)), fixed, change))
        for j, (b, f, frm) in enumerate(versions):
            to = versions[j + 1][2] - timedelta(days=1) if j + 1 < len(versions) else None
            out.append({"fee_schedule_id": fee_schedule_id(len(out) + 1), "merchant_id": m["merchant_id"],
                        "version": j + 1, "fee_rate_bps": b, "fixed_fee_minor": f,
                        "effective_from": frm, "effective_to": to})
    return pd.DataFrame(out)
