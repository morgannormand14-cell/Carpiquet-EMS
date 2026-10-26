"""R25 transition correlation and timeout regression tests."""
import importlib.util
import sys
import types
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
package = "r25_confirmation_pkg"
sys.modules.setdefault(package, types.ModuleType(package))
sys.modules[package].__path__ = [str(root)]


def load(name):
    spec = importlib.util.spec_from_file_location(package + "." + name, root / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load("transition_feedback")
m = load("transition_confirmation_tracker")


def test_confirm_only_post_dispatch():
    p = m.start_tracking(system_id="hyper", transport="LOCAL_MQTT", action="request_discharge", sent_at=100, timeout_s=30, command_id="cmd-1")
    args = dict(now=105, observed_state="discharging", observed_soc=80, minimum_soc=10)
    assert not m.evaluate_confirmation(p, telemetry_at=99, **args).confirmed
    assert not m.evaluate_confirmation(p, telemetry_at=100, **args).confirmed
    assert m.evaluate_confirmation(p, telemetry_at=104, **args).confirmed


def test_timeout_latches_fault_even_if_late_feedback_matches():
    p = m.start_tracking(system_id="solar", transport="LOCAL_HTTP", action="request_standby", sent_at=100, timeout_s=10, command_id="cmd-2")
    result = m.evaluate_confirmation(p, now=111, telemetry_at=110, observed_state="standby", observed_soc=10, minimum_soc=10, observed_power_w=0)
    assert result.fault and not result.confirmed
    assert result.reason == "confirmation_timeout"


def test_standby_requires_zero_and_freshness():
    p = m.start_tracking(system_id="solar", transport="LOCAL_HTTP", action="request_standby", sent_at=100, timeout_s=10, command_id="cmd-3")
    assert not m.evaluate_confirmation(p, now=105, telemetry_at=104, observed_state="standby", observed_soc=10, minimum_soc=10, observed_power_w=None).confirmed
    assert m.evaluate_confirmation(p, now=105, telemetry_at=104, observed_state="standby", observed_soc=10, minimum_soc=10, observed_power_w=0).confirmed


def test_charge_and_off_block_and_invalid_tracking_rejected():
    p = m.start_tracking(system_id="hyper", transport="CLOUD_MQTT", action="request_discharge", sent_at=100, timeout_s=10, command_id="cmd-4")
    for state in ("off", "charging"):
        r = m.evaluate_confirmation(p, now=105, telemetry_at=104, observed_state=state, observed_soc=80, minimum_soc=10)
        assert r.fault
    for timeout in (0, 121):
        try:
            m.start_tracking(system_id="hyper", transport="LOCAL_MQTT", action="request_discharge", sent_at=100, timeout_s=timeout, command_id="cmd")
        except ValueError:
            pass
        else:
            assert False, "Invalid timeout accepted"
