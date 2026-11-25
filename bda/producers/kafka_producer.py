"""Replay generated transactions and synthetic companion events to Kafka."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features.feature_engineering import engineer_offline_features

try:
    from confluent_kafka import Producer
except ImportError:
    Producer = None


TOPIC = "transactions"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def transaction_event(row: pd.Series) -> dict:
    return {
        "txn_id": str(row["txn_id"]),
        "account_id": str(row["account_id"]),
        "amount": float(row["amount"]),
        "currency": str(row["currency"]),
        "timestamp": utc_timestamp(),
        "merchant_id": str(row["merchant_id"]),
        "channel": str(row["channel"]),
        "device_id": str(row["device_id"]),
        "lat": float(row["lat"]),
        "lon": float(row["lon"]),
        "is_new_device": bool(row.get("is_new_device", False)),
        "failed_logins": int(row.get("failed_logins", 0)),
        "ip_reputation": float(row.get("ip_reputation", 0)),
        "vpn_flag": bool(row.get("vpn_flag", False)),
        "blacklisted_ip": bool(row.get("blacklisted_ip", False)),
        "merchant_risk": float(row.get("merchant_risk", 0)),
        "amount_to_account_avg": float(row.get("amount_to_account_avg", 1)),
        "txn_count_60m": int(row.get("txn_count_60m", 1)),
        "failed_logins_before_txn": int(row.get("failed_logins", 0)),
    }


def replay(csv_path: Path, bootstrap: str, count: int, speed: float) -> None:
    if Producer is None:
        raise RuntimeError("confluent-kafka is not installed")
    frame = engineer_offline_features(pd.read_csv(csv_path))
    producer = Producer({"bootstrap.servers": bootstrap})
    rows = frame.head(count).to_dict("records")

    for index, row in enumerate(rows, start=1):
        event = transaction_event(pd.Series(row))
        producer.produce(
            TOPIC,
            key=event["account_id"].encode("utf-8"),
            value=json.dumps(event).encode("utf-8"),
        )
        if index % 100 == 0:
            producer.flush()
        time.sleep(1.0 / max(speed, 0.01))
    producer.flush()


def companion_events(bootstrap: str, count: int) -> None:
    """Publish device, location, behaviour and network examples for manual checkpoints."""
    if Producer is None:
        raise RuntimeError("confluent-kafka is not installed")
    producer = Producer({"bootstrap.servers": bootstrap})
    for index in range(count):
        account = f"A{random.randint(0, 499):04d}"
        txid = f"T{uuid.uuid4().hex[:8]}"
        events = [
            ("device-events", {"device_id": f"D{random.randint(0, 699):04d}", "account_id": account, "os": "Android", "is_new_device": random.random() < 0.1, "timestamp": utc_timestamp()}),
            ("location-events", {"account_id": account, "txn_id": txid, "lat": random.uniform(-60, 60), "lon": random.uniform(-180, 180), "ip_country": random.choice(["US", "IN", "GB"]), "city": "Synthetic", "timestamp": utc_timestamp()}),
            ("behaviour-logs", {"account_id": account, "txn_id": txid, "session_length": random.uniform(10, 1200), "failed_logins": random.randint(0, 5), "typing_speed": random.uniform(0.2, 1.5), "timestamp": utc_timestamp()}),
            ("network-events", {"account_id": account, "txn_id": txid, "ip_reputation": round(random.random(), 3), "vpn_flag": random.random() < 0.1, "blacklisted_ip": random.random() < 0.02, "timestamp": utc_timestamp()}),
        ]
        for topic, event in events:
            producer.produce(topic, key=account.encode(), value=json.dumps(event).encode())
    producer.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--csv", type=Path, default=Path("data/transactions.csv"))
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--speed", type=float, default=10.0)
    args = parser.parse_args()
    replay(args.csv, args.bootstrap, args.count, args.speed)


if __name__ == "__main__":
    main()
