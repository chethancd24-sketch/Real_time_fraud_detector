from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from pymongo import ASCENDING, MongoClient


class MongoAlertWriter:
    def __init__(self, uri: str = "mongodb://localhost:27017", database: str = "fraud") -> None:
        self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.collection = self.client[database]["alerts"]
        self.collection.create_index([("account_id", ASCENDING), ("timestamp", ASCENDING)])
        self.collection.create_index("timestamp", expireAfterSeconds=60 * 60 * 24 * 30)

    def write(self, event: dict) -> None:
        if event.get("risk_level") not in {"Suspicious", "High Risk"}:
            return
        document = dict(event)
        document.setdefault("timestamp", datetime.now(timezone.utc))
        self.collection.update_one(
            {"txn_id": document["txn_id"]},
            {"$set": document},
            upsert=True,
        )

    def write_batch(self, events: Iterable[dict]) -> int:
        count = 0
        for event in events:
            self.write(event)
            count += 1
        return count
