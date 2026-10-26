"""Pack state eligibility tests; no HA or hardware dependencies."""
import importlib.util
from pathlib import Path

module_path = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/pack_state_supervisor.py"
spec = importlib.util.spec_from_file_location("pack_state_supervisor", module_path)
import sys
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
evaluate_pack = module.evaluate_pack


def test_charging_and_off_are_excluded_at_any_soc():
    for state in ("1", "3"):
        for soc in (10, 50, 100):
            result = evaluate_pack(state, soc, 10)
            assert not result.eligible
            assert not result.needs_discharge_transition


def test_standby_requires_transition_before_eligibility():
    result = evaluate_pack("0", 18, 10)
    assert not result.eligible
    assert result.needs_discharge_transition


def test_minimum_soc_requests_standby():
    result = evaluate_pack("2", 10, 10)
    assert not result.eligible
    assert result.needs_standby_transition


def test_discharge_only_when_above_minimum():
    assert evaluate_pack("2", 18, 10).eligible
    assert not evaluate_pack("2", 9, 10).eligible


def test_unknown_and_missing_are_excluded():
    for state in (None, "unknown", "unavailable", "4", "-1"):
        assert not evaluate_pack(state, 50, 10).eligible


def test_recovery_without_restart():
    states = [("2", 10), ("0", 15), ("2", 15), ("1", 16), ("0", 18), ("2", 18)]
    actual = [evaluate_pack(state, soc, 10).eligible for state, soc in states]
    assert actual == [False, False, True, False, False, True]


def test_localized_home_assistant_pack_labels():
    for raw in ("0", "standby", "En veille"):
        assert evaluate_pack(raw, 40, 10).needs_discharge_transition
    for raw in ("1", "charging", "En charge"):
        assert not evaluate_pack(raw, 40, 10).eligible
    for raw in ("2", "discharging", "En décharge"):
        assert evaluate_pack(raw, 40, 10).eligible
    for raw in ("3", "off", "Arrêt"):
        assert not evaluate_pack(raw, 40, 10).eligible
    assert not evaluate_pack("unavailable", 40, 10).eligible
