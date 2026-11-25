import pandas as pd

from features.feature_engineering import haversine_km, engineer_offline_features


def test_haversine_zero_for_same_location():
    assert haversine_km(10, 20, 10, 20) == 0


def test_engineer_offline_features_has_model_columns():
    frame = pd.DataFrame([
        {"txn_id": "T1", "account_id": "A1", "amount": 100, "timestamp": "2026-01-01 10:00:00",
         "is_new_device": True, "failed_logins": 2, "ip_reputation": 0.2, "vpn_flag": False},
        {"txn_id": "T2", "account_id": "A1", "amount": 200, "timestamp": "2026-01-01 10:30:00",
         "is_new_device": False, "failed_logins": 0, "ip_reputation": 0.1, "vpn_flag": False},
    ])
    result = engineer_offline_features(frame)
    assert "amount_to_account_avg" in result
    assert "txn_count_60m" in result
