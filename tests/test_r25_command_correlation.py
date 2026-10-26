"""Offline R25 command/telemetry correlation tests."""
import importlib.util
import sys
import types
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
pkg = "r25_correlation_pkg"
package = types.ModuleType(pkg)
package.__path__ = [str(root)]
sys.modules[pkg] = package


def load(name):
    spec = importlib.util.spec_from_file_location(pkg + "." + name, root / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load("transition_feedback")
load("transition_confirmation_tracker")
correlate = load("r25_command_correlation").correlate_transition

BASE = dict(system_id="hyper_2000", transport="LOCAL_MQTT",
            action="request_discharge", command_id="c1", dispatched=True,
            sent_at=100, transport_accepted=True, now=105, telemetry_at=104,
            observed_state="discharging", observed_soc=80, minimum_soc=10)


def test_both_mqtt_routes_require_proven_dispatch():
    for transport in ("LOCAL_MQTT", "CLOUD_MQTT"):
        assert correlate(**(BASE | {"transport": transport})).confirmed
        assert not correlate(**(BASE | {"transport": transport, "dispatched": False})).confirmed
        assert not correlate(**(BASE | {"transport": transport, "command_id": None})).confirmed


def test_http_ack_does_not_prove_pack_state():
    args = BASE | dict(system_id="solarflow_2400_pro", transport="ZenSDK")
    assert correlate(**(args | {"observed_state": "standby"})).state == "PENDING"
    assert correlate(**(args | {"telemetry_at": 99})).state == "PENDING"
    assert correlate(**(args | {"transport_accepted": False})).state == "PENDING"
    assert correlate(**args).confirmed


def test_timeout_and_invalid_transport_fail_closed():
    assert correlate(**(BASE | {"now": 140, "telemetry_at": 139})).fault
    assert not correlate(**(BASE | {"transport": "ZenSDK"})).confirmed
    assert not correlate(**(BASE | {"observed_soc": 10})).confirmed
    assert not correlate(**(BASE | {"sent_at": None})).confirmed


def test_standby_needs_fresh_state_and_zero_power():
    args = BASE | dict(action="request_standby", observed_state="standby")
    assert not correlate(**args).confirmed
    assert correlate(**(args | {"observed_power_w": 0})).confirmed
