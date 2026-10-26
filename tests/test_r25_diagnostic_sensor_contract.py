"""Read-only R25 diagnostic sensor contract."""
from pathlib import Path


def test_diagnostic_sensor_exposes_bounded_nonsecret_fields():
    src = (Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/sensor.py").read_text()
    assert '("r25_diagnostic", "R25 Diagnostic", "r25_cycle_mode", None, None)' in src
    assert 'if self._data_key == "r25_cycle_mode":' in src
    for field in ("cycle_ready", "transition_execution", "watchdog_state", "http_result",
                  "http_requested_w", "http_observed_w", "http_verified",
                  "http_zero_verified", "hyper_transition_state",
                  "solarflow_transition_state", "hyper_telemetry_available",
                  "solarflow_telemetry_available"):
        assert '"' + field + '"' in src
    assert '"http_error"' not in src
    assert '"mqtt_payload"' not in src
