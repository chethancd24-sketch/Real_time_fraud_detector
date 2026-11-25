from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def write_scored_batch(events: Iterable[dict], output: str | Path) -> Path:
    frame = pd.DataFrame(events)
    if frame.empty:
        return Path(output)
    timestamp = pd.to_datetime(frame.get("timestamp"), utc=True, errors="coerce")
    date = timestamp.dt.strftime("%Y-%m-%d").fillna("unknown")
    root = Path(output)
    for partition, partition_frame in frame.groupby(date):
        destination = root / f"date={partition}"
        destination.mkdir(parents=True, exist_ok=True)
        filename = destination / "scored.parquet"
        if filename.exists():
            existing = pd.read_parquet(filename)
            combined = pd.concat([existing, partition_frame], ignore_index=True)
            combined.drop_duplicates(subset=["txn_id"], keep="last", inplace=True)
            combined.to_parquet(filename, index=False)
        else:
            partition_frame.to_parquet(filename, index=False)
    return root
