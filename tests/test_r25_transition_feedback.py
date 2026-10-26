"""Offline transition confirmation tests."""
import importlib.util
import sys
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/transition_feedback.py"
spec = importlib.util.spec_from_file_location("r25_transition_feedback", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
verify = module.verify_transition


def test_discharge_requires_fresh_discharge_state_and_soc():
    kwargs = dict(action="request_discharge", observed_soc=25, minimum_soc=10)
    assert verify(**kwargs, observed_state="discharging", fresh=True).confirmed
    assert not verify(**kwargs, observed_state="standby", fresh=True).confirmed
    assert not verify(**kwargs, observed_state="discharging", fresh=False).confirmed
    assert not verify(**{**kwargs, "observed_soc": 10}, observed_state="discharging", fresh=True).confirmed


def test_standby_requires_state_and_zero_readback():
    kwargs = dict(action="request_standby", observed_soc=10, minimum_soc=10, fresh=True)
    assert verify(**kwargs, observed_state="standby", observed_power_w=0).confirmed
    assert not verify(**kwargs, observed_state="standby", observed_power_w=30).confirmed
    assert not verify(**kwargs, observed_state="discharging", observed_power_w=0).confirmed
    assert not verify(**kwargs, observed_state="standby", observed_power_w=None).confirmed


def test_off_and_charging_are_never_confirmed():
    for state in ("off", "charging", "unknown", None):
        for action in ("request_standby", "request_discharge"):
            assert not verify(action, observed_state=state, fresh=True, observed_soc=80, minimum_soc=10, observed_power_w=0).confirmed
