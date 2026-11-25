from __future__ import annotations

import logging
from pathlib import Path

import joblib
import pandas as pd

from rules.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class FraudScorer:
    def __init__(self, artifact_dir: str | Path = "ml/artifacts") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.rule_engine = RuleEngine()
        supervised_path = self.artifact_dir / "supervised.joblib"
        anomaly_path = self.artifact_dir / "anomaly.joblib"
        features_path = self.artifact_dir / "features.joblib"
        if supervised_path.exists() and anomaly_path.exists():
            self.supervised = joblib.load(supervised_path)
            self.anomaly = joblib.load(anomaly_path)
            self.features = joblib.load(features_path)
            logger.info("Loaded trained fraud model artifacts from %s", self.artifact_dir)
        else:
            self.supervised = None
            self.anomaly = None
            self.features = None
            logger.warning(
                "Model artifacts not found in %s; using the deterministic baseline scorer",
                self.artifact_dir,
            )

    def score(self, event: dict) -> dict:
        if self.supervised is not None:
            frame = pd.DataFrame([event])
            frame = frame.reindex(columns=self.features)
            defaults = {
                "amount_to_account_avg": 1.0,
                "txn_count_60m": 1.0,
                "failed_logins_before_txn": event.get("failed_logins", 0),
            }
            for name in self.features:
                if name not in event:
                    frame[name] = defaults.get(name, 0)
            frame = frame.fillna(0)
            ml_score = float(self.supervised.predict_proba(frame)[:, 1][0])
            raw = float(-self.anomaly.score_samples(frame)[0])
            anomaly_score = min(1.0, max(0.0, (raw + 0.5)))
        else:
            # Deterministic baseline until the offline model is trained.
            ml_score = min(1.0, (
                float(event.get("amount", 0)) / 1000
                + float(event.get("is_new_device", 0)) * 0.25
                + float(event.get("failed_logins", 0)) * 0.08
            ))
            anomaly_score = min(1.0, float(event.get("ip_reputation", 0)))
        return self.rule_engine.classify(ml_score, anomaly_score, event)
