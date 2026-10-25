"""No hardware command may originate from pack transition planning."""
import importlib.util
import sys
import types
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
pkg = types.ModuleType("r25pack")
pkg.__path__ = [str(root)]
sys.modules["r25pack"] = pkg
for name in ("pack_state_supervisor", "pack_transition_controller"):
    spec = importlib.util.spec_from_file_location("r25pack." + name, root / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

evaluate_pack = sys.modules["r25pack.pack_state_supervisor"].evaluate_pack
plan_transition = sys.modules["r25pack.pack_transition_controller"].plan_transition


def test_standby_above_reserve_requests_discharge_only_when_needed():
    pack = evaluate_pack(0, 20, 10)
    assert plan_transition("hyper_2000", pack, discharge_needed=True).action == "request_discharge"
    assert plan_transition("hyper_2000", pack, discharge_needed=False).action == "none"


def test_discharge_at_minimum_requests_standby():
    pack = evaluate_pack(2, 10, 10)
    assert plan_transition("solarflow_2400_pro", pack, discharge_needed=True).action == "request_standby"


def test_off_charging_and_unknown_are_never_reactivated():
    for raw in (1, 3, None, "unknown"):
        pack = evaluate_pack(raw, 80, 10)
        assert plan_transition("hyper_2000", pack, discharge_needed=True).action == "none"


def test_intents_are_always_simulated():
    for raw in (0, 1, 2, 3):
        intent = plan_transition("solarflow_2400_pro", evaluate_pack(raw, 20, 10), discharge_needed=True)
        assert intent.simulated is True
