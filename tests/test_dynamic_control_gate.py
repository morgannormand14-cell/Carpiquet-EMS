"""R25 fail-closed dynamic gate regression tests (no device required)."""
import importlib.util
from pathlib import Path
import sys

module_path = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/dynamic_control_gate.py"
spec = importlib.util.spec_from_file_location("dynamic_control_gate_under_test", module_path)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def decide(**overrides):
    values = dict(requested_w=300, limit_w=680, local_mode=True,
                  transport_qualified=True, soc_valid=True,
                  authorized=True, previously_active=False)
    values.update(overrides)
    return gate.evaluate_dynamic_gate(**values)


def test_nominal_remains_shadow():
    result = decide()
    assert result.state == "READY_SHADOW"
    assert result.target_w == 300
    assert not result.should_write


def test_no_authorization_locks():
    assert decide(authorized=False).state == "LOCKED"


def test_loss_of_transport_requires_stop():
    result = decide(transport_qualified=False, previously_active=True)
    assert result.must_stop and not result.should_write


def test_soc_loss_requires_stop():
    assert decide(soc_valid=False, previously_active=True).must_stop


def test_out_of_bounds_fails_closed():
    assert decide(requested_w=700).state == "LOCKED"
    assert decide(requested_w=float("nan")).state == "LOCKED"


def test_zero_requests_stop():
    assert decide(requested_w=0, previously_active=True).must_stop


def test_deadband_does_not_rewrite():
    result = decide(requested_w=304, last_command_w=300, previously_active=True)
    assert result.state == "UNCHANGED" and not result.should_write
