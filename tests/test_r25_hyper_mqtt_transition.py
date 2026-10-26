"""Offline Hyper 2000 MQTT command-contract tests."""
import importlib.util
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/hyper_mqtt_transition.py"
spec = importlib.util.spec_from_file_location("r25_hyper_mqtt_transition", p)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_both_transport_profiles_prepare_identical_zendure_command():
    local = mod.prepare_hyper_transition("request_discharge", transport="LOCAL_MQTT", power_w=100, pack_state="standby", soc=20, minimum_soc=10)
    cloud = mod.prepare_hyper_transition("request_discharge", transport="CLOUD_MQTT", power_w=100, pack_state="standby", soc=20, minimum_soc=10)
    assert local.allowed and cloud.allowed
    assert local.payload == cloud.payload
    assert local.payload["function"] == "deviceAutomation"
    assert local.payload["arguments"][0]["autoModelProgram"] == 2
    assert local.payload["arguments"][0]["autoModelValue"]["outPower"] == 100
    assert not local.write_enabled and not cloud.write_enabled


def test_standby_is_not_mistaken_for_power_off():
    for transport in mod.TRANSPORTS:
        prepared = mod.prepare_hyper_transition("request_standby", transport=transport, pack_state="discharging", soc=10, minimum_soc=10)
        assert not prepared.allowed and prepared.payload is None


def test_fail_closed_on_off_charging_unknown_or_soc_minimum():
    for state in ("off", "charging", "unknown", "discharging"):
        cmd = mod.prepare_hyper_transition("request_discharge", transport="LOCAL_MQTT", power_w=100, pack_state=state, soc=50, minimum_soc=10)
        assert not cmd.allowed
    cmd = mod.prepare_hyper_transition("request_discharge", transport="LOCAL_MQTT", power_w=100, pack_state="standby", soc=10, minimum_soc=10)
    assert not cmd.allowed


def test_reject_unqualified_transport_and_invalid_power():
    for power in (0, -1, 1201, 100.5):
        cmd = mod.prepare_hyper_transition("request_discharge", transport="CLOUD_MQTT", power_w=power, pack_state="standby", soc=50, minimum_soc=10)
        assert not cmd.allowed
    assert not mod.prepare_hyper_transition("request_discharge", transport="LOCAL_HTTP", power_w=100, pack_state="standby", soc=50, minimum_soc=10).allowed
