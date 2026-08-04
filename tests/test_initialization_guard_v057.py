from pathlib import Path

def test_initialization_guard_present():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(
        encoding="utf-8"
    )
    assert "_async_wait_for_valid_initialization" in source
    assert "SOC invalide ou nul" in source
    assert "DEFAULT_INITIALIZATION_TIMEOUT_SECONDS" in source
    assert "self._automation_enabled_runtime = False" in source

def test_dashboard_exposes_initialization_diagnostics():
    source = Path("dashboards/carpiquet_ems.yaml").read_text(encoding="utf-8")
    assert "sensor.carpiquet_ems_engine_initialization_state" in source
    assert "binary_sensor.carpiquet_ems_engine_initialization_ready" in source
    assert "sensor.carpiquet_ems_engine_initialization_error" in source
