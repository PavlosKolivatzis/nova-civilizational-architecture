from slots.slot07_production_controls.production_control_engine import ProductionControlEngine


def test_active_safeguards_reflect_configuration():
    base_config = {
        "enabled": True,
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 5,
            "error_threshold": 0.5,
            "reset_timeout": 0.1,
            "recovery_time": 60,
        },
        "rate_limiting": {
            "enabled": False,
            "requests_per_minute": 60,
            "burst_size": 5,
        },
        "resource_protection": {
            "enabled": False,
            "max_payload_size_mb": 1,
            "max_processing_time_seconds": 1,
            "max_concurrent_requests": 1,
        },
        "monitoring": {
            "health_check_enabled": True,
            "health_check_interval": 10,
            "metrics_collection_enabled": False,
            "alert_on_circuit_breaker_trip": False,
        },
        "failover": {
            "enabled": False,
            "backup_mode_enabled": False,
            "graceful_degradation_enabled": False,
        },
    }
    engine = ProductionControlEngine(base_config)
    active = engine._get_active_safeguards()
    assert "circuit_breaker(closed)" in active
    assert "rate_limiting" not in active
    assert "resource_protection" not in active

    base_config["rate_limiting"]["enabled"] = True
    base_config["resource_protection"]["enabled"] = True
    engine2 = ProductionControlEngine(base_config)
    active2 = engine2._get_active_safeguards()
    assert "rate_limiting" in active2
    assert "resource_protection" in active2

