from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import yaml


DEFAULT_RULES = {
    "rules": [
        {"id": "blacklisted_ip", "weight": 1.0},
        {"id": "new_device_large_amount", "weight": 0.9},
        {"id": "impossible_travel", "weight": 0.95},
        {"id": "rapid_fire", "weight": 0.75},
        {"id": "failed_logins", "weight": 0.65},
        {"id": "vpn_high_risk", "weight": 0.7},
    ],
    "weights": {"ml": 0.55, "anomaly": 0.20, "rules": 0.25},
    "thresholds": {"legitimate_max": 0.35, "suspicious_max": 0.75},
}


class RuleEngine:
    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is None:
            config_path = Path(__file__).with_name("rules.yaml")
        path = Path(config_path)
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                self.config = yaml.safe_load(handle)
        else:
            self.config = DEFAULT_RULES

    def triggered_rules(self, event: Mapping) -> list[str]:
        fired: list[str] = []
        amount = float(event.get("amount", 0) or 0)
        if event.get("blacklisted_ip"):
            fired.append("blacklisted_ip")
        if event.get("is_new_device") and amount >= 800:
            fired.append("new_device_large_amount")
        if float(event.get("distance_km", 0) or 0) > 1000:
            fired.append("impossible_travel")
        if int(event.get("txn_count_60m", 0) or 0) > 5:
            fired.append("rapid_fire")
        if int(event.get("failed_logins", 0) or 0) >= 4:
            fired.append("failed_logins")
        if event.get("vpn_flag") and amount >= 500:
            fired.append("vpn_high_risk")
        return fired

    def score(self, event: Mapping) -> tuple[float, list[str]]:
        weights = {item["id"]: float(item["weight"]) for item in self.config["rules"]}
        fired = self.triggered_rules(event)
        if not fired:
            return 0.0, fired
        return min(1.0, max(weights[name] for name in fired)), fired

    def classify(
        self,
        ml_score: float,
        anomaly_score: float,
        event: Mapping,
    ) -> dict:
        rule_score, fired = self.score(event)
        weights = self.config["weights"]
        final_score = (
            float(weights["ml"]) * float(ml_score)
            + float(weights["anomaly"]) * float(anomaly_score)
            + float(weights["rules"]) * rule_score
        )
        thresholds = self.config["thresholds"]
        if final_score < float(thresholds["legitimate_max"]):
            risk_level = "Legitimate"
        elif final_score <= float(thresholds["suspicious_max"]):
            risk_level = "Suspicious"
        else:
            risk_level = "High Risk"
        return {
            "risk_score": round(final_score, 6),
            "risk_level": risk_level,
            "ml_score": float(ml_score),
            "anomaly_score": float(anomaly_score),
            "rule_score": rule_score,
            "triggered_rules": fired,
        }
