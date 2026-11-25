"""Reusable feature helpers shared by offline training and streaming."""

from __future__ import annotations

import math
from typing import Iterable

import pandas as pd


MODEL_FEATURES = [
    "amount",
    "amount_to_account_avg",
    "txn_count_60m",
    "is_new_device",
    "failed_logins",
    "ip_reputation",
    "vpn_flag",
    "merchant_risk",
    "failed_logins_before_txn",
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if any(value is None for value in (lat1, lon1, lat2, lon2)):
        return 0.0
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(min(1.0, a)))


def engineer_offline_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce")
    result["amount"] = pd.to_numeric(result["amount"], errors="coerce").fillna(0).clip(lower=0)
    result["account_avg"] = result.groupby("account_id", sort=False)["amount"].transform("mean")
    result["amount_to_account_avg"] = (result["amount"] / result["account_avg"].replace(0, 1)).fillna(1)
    result["txn_count_60m"] = 1.0
    if len(result):
        result = result.sort_values("timestamp")
        for account_id, account_rows in result.groupby("account_id", sort=False):
            indexed = account_rows.set_index("timestamp")
            counts = indexed["txn_id"].rolling("60min").count()
            counts.index = account_rows["timestamp"]
            result.loc[account_rows.index, "txn_count_60m"] = counts.to_numpy()
    result["is_new_device"] = result.get("is_new_device", False).astype(bool).astype(int)
    result["failed_logins"] = pd.to_numeric(result.get("failed_logins", 0), errors="coerce").fillna(0)
    result["failed_logins_before_txn"] = result["failed_logins"]
    result["ip_reputation"] = pd.to_numeric(result.get("ip_reputation", 0), errors="coerce").fillna(0)
    result["vpn_flag"] = result.get("vpn_flag", False).astype(bool).astype(int)
    merchant_risk = result["merchant_risk"] if "merchant_risk" in result else pd.Series(0.0, index=result.index)
    result["merchant_risk"] = pd.to_numeric(merchant_risk, errors="coerce").fillna(0)
    return result
