"""Contract tests for Carpiquet EMS R25 privacy-safe diagnostics.

Run with: python -m pytest -q tests/test_r25_diagnostics_security.py
"""
import asyncio
import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys


def _load_diagnostics():
    root = Path(__file__).resolve().parents[1]
    source = root / "custom_components" / "carpiquet_ems" / "diagnostics.py"
    # Load the module without importing the whole Home Assistant integration.
    package = "_r25_diagnostics_test_package"
    pkg = ModuleType(package)
    pkg.__path__ = [str(source.parent)]
    const = ModuleType(f"{package}.const")
    const.DOMAIN = "carpiquet_ems"
    const.VERSION = "test-version"
    sys.modules[package] = pkg
    sys.modules[f"{package}.const"] = const
    spec = importlib.util.spec_from_file_location(f"{package}.diagnostics", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_export_is_whitelisted_and_redacts_secrets():
    diagnostics = _load_diagnostics()
    secret = "VERY_PRIVATE_PASSWORD_123"
    entry = SimpleNamespace(
        entry_id="entry-1",
        data={"password": secret, "mqtt_token": secret, "device_serial": secret},
        options={"api_key": secret, "endpoint": f"https://{secret}.invalid"},
    )
    coordinator = SimpleNamespace(data={
        "r25_cycle_mode": "Simulation",
        "r25_cycle_ready": False,
        "r25_watchdog_state": "LOCKED",
        "r25_http_result": "NOT_RUN",
        "r25_http_setpoint_feedback": {
            "state": "NOT_RUN", "requested_w": 0.0, "observed_w": 0.0,
            "verified": False, "error": secret, "transport_url": secret,
            "payload": {"password": secret},
        },
        "r25_pack_transition_feedback": {
            "hyper_2000": {"state": "PENDING", "confirmed": False, "reason": secret},
            "solarflow_2400_pro": {"state": "BLOCKED", "confirmed": False},
            "unrecognized_system": {"password": secret},
        },
        "r25_transition_telemetry": {
            "hyper_2000": {"entity_available": True, "last_updated": secret,
                           "confirmation_state": "NOT_TRACKED", "reason": secret},
        },
        "raw_http_envelope": {"token": secret},
        "password": secret,
    })
    hass = SimpleNamespace(data={"carpiquet_ems": {entry.entry_id: coordinator}})
    result = asyncio.run(diagnostics.async_get_config_entry_diagnostics(hass, entry))
    serialized = json.dumps(result)
    assert secret not in serialized
    assert "password" not in serialized
    assert "mqtt_token" not in serialized
    assert "transport_url" not in serialized
    assert "raw_http_envelope" not in serialized
    assert "last_updated" not in serialized
    assert result["state"]["r25_cycle_mode"] == "Simulation"
    assert result["state"]["r25_http_setpoint_feedback"]["verified"] is False
    assert result["state"]["r25_transition_telemetry"]["hyper_2000"]["entity_available"] is True
    assert "unrecognized_system" not in result["state"]["r25_pack_transition_feedback"]


def test_unexpected_shapes_are_ignored():
    diagnostics = _load_diagnostics()
    entry = SimpleNamespace(entry_id="entry-2", data={}, options={})
    coordinator = SimpleNamespace(data={
        "r25_cycle_mode": {"unexpected": "nested"},
        "r25_http_setpoint_feedback": ["invalid"],
        "r25_transition_telemetry": "invalid",
        "r25_pack_transition_feedback": {"hyper_2000": ["invalid"]},
    })
    hass = SimpleNamespace(data={"carpiquet_ems": {entry.entry_id: coordinator}})
    result = asyncio.run(diagnostics.async_get_config_entry_diagnostics(hass, entry))
    assert "r25_cycle_mode" not in result["state"]
    assert result["state"]["r25_http_setpoint_feedback"] == {}
    assert result["state"]["r25_transition_telemetry"] == {}
    assert result["state"]["r25_pack_transition_feedback"]["hyper_2000"] == {}
