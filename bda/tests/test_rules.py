from rules.rule_engine import RuleEngine


def test_blacklisted_ip_is_high_risk():
    engine = RuleEngine()
    result = engine.classify(0.9, 0.9, {"amount": 100, "blacklisted_ip": True})
    assert result["risk_level"] == "High Risk"
    assert "blacklisted_ip" in result["triggered_rules"]


def test_empty_event_is_legitimate():
    engine = RuleEngine()
    result = engine.classify(0.1, 0.1, {})
    assert result["risk_level"] == "Legitimate"


def test_new_device_large_amount_trigger():
    engine = RuleEngine()
    result = engine.classify(0.5, 0.5, {"amount": 900, "is_new_device": True})
    assert "new_device_large_amount" in result["triggered_rules"]
