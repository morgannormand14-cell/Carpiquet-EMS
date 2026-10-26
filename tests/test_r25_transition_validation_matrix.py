"""R25 offline validation matrix; never contacts an inverter."""
import importlib.util
import sys
import types
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
pkg = "r25_validation_matrix"
sys.modules.setdefault(pkg, types.ModuleType(pkg))
sys.modules[pkg].__path__ = [str(root)]


def load(name):
    spec = importlib.util.spec_from_file_location(pkg + "." + name, root / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


feedback = load("transition_feedback")
tracker = load("transition_confirmation_tracker")
pack = load("pack_state_supervisor")
planner = load("pack_transition_controller")


def test_standby_not_eligible_until_confirmed_discharge():
    candidate = pack.evaluate_pack(0, 70, 15)
    assert not candidate.eligible and candidate.needs_discharge_transition
    intent = planner.plan_transition("hyper", candidate, discharge_needed=True)
    assert intent.action == "request_discharge" and intent.simulated
    active = pack.evaluate_pack(2, 70, 15)
    assert active.eligible and not active.needs_discharge_transition


def test_minimum_soc_requires_standby_but_does_not_send():
    state = pack.evaluate_pack(2, 15, 15)
    intent = planner.plan_transition("solar", state, discharge_needed=True)
    assert not state.eligible and intent.action == "request_standby" and intent.simulated


def test_off_and_charging_never_produce_transition():
    for raw in (1, 3, "unavailable"):
        state = pack.evaluate_pack(raw, 80, 15)
        intent = planner.plan_transition("hyper", state, discharge_needed=True)
        assert intent.action == "none" and not state.eligible


def test_post_command_confirmation_and_timeout():
    pending = tracker.start_tracking(system_id="hyper", transport="LOCAL_MQTT", action="request_discharge", sent_at=50, timeout_s=10, command_id="test")
    base = dict(observed_state="discharging", observed_soc=70, minimum_soc=15)
    assert not tracker.evaluate_confirmation(pending, now=55, telemetry_at=50, **base).confirmed
    assert tracker.evaluate_confirmation(pending, now=55, telemetry_at=54, **base).confirmed
    assert tracker.evaluate_confirmation(pending, now=61, telemetry_at=60, **base).fault


def test_standby_requires_zero_output():
    pending = tracker.start_tracking(system_id="solar", transport="LOCAL_HTTP", action="request_standby", sent_at=50, timeout_s=10, command_id="test-zero")
    base = dict(now=55, telemetry_at=54, observed_state="standby", observed_soc=15, minimum_soc=15)
    assert not tracker.evaluate_confirmation(pending, observed_power_w=5, **base).confirmed
    assert tracker.evaluate_confirmation(pending, observed_power_w=0, **base).confirmed
