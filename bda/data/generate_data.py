"""Generate an historical labelled base dataset and synthetic companion events."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


MERCHANT_CATEGORIES = ["grocery", "travel", "electronics", "food", "gaming"]
COUNTRIES = ["US", "GB", "IN", "DE", "FR", "BR"]


def generate(count: int, seed: int, output: Path) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    random.seed(seed)
    output.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 1, 1)
    timestamps = [start + timedelta(minutes=int(x)) for x in rng.integers(0, 60 * 24 * 30, count)]

    rows = {
        "txn_id": [f"T{index:08d}" for index in range(count)],
        "account_id": [f"A{index % 500:04d}" for index in range(count)],
        "amount": rng.lognormal(mean=3.4, sigma=1.1, size=count).round(2),
        "currency": np.random.choice(["USD", "EUR", "GBP", "INR"], count),
        "timestamp": timestamps,
        "merchant_id": [f"M{index % 100:04d}" for index in range(count)],
        "device_id": [f"D{index % 700:04d}" for index in range(count)],
        "channel": np.random.choice(["web", "mobile", "pos"], count),
        "country": np.random.choice(COUNTRIES, count),
        "is_new_device": rng.choice([False, False, False, True], count),
        "failed_logins": rng.integers(0, 5, count),
        "ip_reputation": rng.uniform(0, 1, count).round(3),
        "vpn_flag": rng.choice([False, True], count, p=[0.9, 0.1]),
        "lat": rng.uniform(-60, 60, count).round(5),
        "lon": rng.uniform(-180, 180, count).round(5),
    }
    frame = pd.DataFrame(rows)
    frame["fraud"] = 0

    # Inject explainable, realistic fraud patterns.
    fraud_mask = np.zeros(count, dtype=bool)
    if count >= 10:
        candidates = rng.integers(0, count, max(1, count // 100))
        fraud_mask[candidates] = True
    fraud_mask |= (frame["amount"] > 800) & frame["is_new_device"]
    fraud_mask |= (frame["failed_logins"] >= 4) & (frame["ip_reputation"] > 0.7)
    fraud_mask |= frame["vpn_flag"] & (frame["amount"] > 500)
    frame.loc[fraud_mask, "fraud"] = 1
    frame.sort_values("timestamp", inplace=True)
    frame.to_csv(output / "transactions.csv", index=False)
    frame.to_parquet(output / "transactions.parquet", index=False)

    merchants = pd.DataFrame(
        [
            {
                "merchant_id": f"M{index:04d}",
                "category": MERCHANT_CATEGORIES[index % len(MERCHANT_CATEGORIES)],
                "risk_score": round(rng.uniform(0, 1), 3),
                "country": COUNTRIES[index % len(COUNTRIES)],
            }
            for index in range(100)
        ]
    )
    merchants.to_csv(output / "merchants.csv", index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data"))
    args = parser.parse_args()
    frame = generate(args.count, args.seed, args.output)
    print(f"Generated {len(frame)} transactions ({int(frame['fraud'].sum())} injected fraud)")


if __name__ == "__main__":
    main()
