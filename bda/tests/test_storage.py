from pathlib import Path

from storage.hdfs_writer import write_scored_batch


def test_hdfs_writer_creates_partition(tmp_path):
    events = [{
        "txn_id": "T1",
        "timestamp": "2026-01-01T10:00:00Z",
        "risk_level": "High Risk",
    }]
    root = write_scored_batch(events, tmp_path)
    assert (root / "date=2026-01-01" / "scored.parquet").exists()
