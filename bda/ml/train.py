from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import train_test_split

from features.feature_engineering import MODEL_FEATURES, engineer_offline_features


def train(csv_path: Path, artifact_dir: Path) -> dict:
    frame = pd.read_csv(csv_path)
    if "fraud" not in frame.columns:
        raise ValueError("Historical data must contain a 'fraud' label")

    frame = engineer_offline_features(frame)
    frame.sort_values("timestamp", inplace=True)
    cut = int(len(frame) * 0.8)
    train_frame = frame.iloc[:cut]
    test_frame = frame.iloc[cut:]

    x_train = train_frame[MODEL_FEATURES].fillna(0)
    y_train = train_frame["fraud"].astype(int)
    x_test = test_frame[MODEL_FEATURES].fillna(0)
    y_test = test_frame["fraud"].astype(int)

    supervised = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    supervised.fit(x_train, y_train)
    probabilities = supervised.predict_proba(x_test)[:, 1]

    anomaly = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
    anomaly.fit(x_train)
    raw_anomaly = -anomaly.score_samples(x_test)
    anomaly_scores = (raw_anomaly - raw_anomaly.min()) / (raw_anomaly.max() - raw_anomaly.min() + 1e-9)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(supervised, artifact_dir / "supervised.joblib")
    joblib.dump(anomaly, artifact_dir / "anomaly.joblib")
    joblib.dump(MODEL_FEATURES, artifact_dir / "features.joblib")

    pr_auc = average_precision_score(y_test, probabilities)
    precision, recall, thresholds = precision_recall_curve(y_test, probabilities)
    return {
        "train_rows": len(train_frame),
        "test_rows": len(test_frame),
        "pr_auc": round(float(pr_auc), 6),
        "precision": round(float(precision[-1]), 6),
        "recall": round(float(recall[-1]), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("data/transactions.csv"))
    parser.add_argument("--artifacts", type=Path, default=Path("ml/artifacts"))
    args = parser.parse_args()
    print(train(args.csv, args.artifacts))


if __name__ == "__main__":
    main()
