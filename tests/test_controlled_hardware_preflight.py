"""3B-21 final hardware preflight audit tests."""
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems" / "controlled_hardware_preflight.py"
spec = importlib.util.spec_from_file_location("controlled_hardware_preflight", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def baseline(**overrides):
    values = dict(
        final_regression_passed=True, locked_chain_consistent=True,
        safety_invariants_preserved=True, simulation_bench_passed=True,
        independent_evidence_complete=False, final_write_locked=True,
        final_reinjection_allowed=False, real_write_used=False,
        test_power_w=50.0, duration_seconds=5.0, single_device_only=True,
        local_http_only=True, watchdog_required=True, verification_required=True,
        zero_return_required=True, zero_on_failure_required=True,
        relock_required=True, test_request_prepared=True, zero_request_prepared=True,
        report_target_ready=True, test_armed=True, solarflow_selected=True,
        local_http_qualified=True, explicit_write_authorized=False,
    )
    values.update(overrides)
    return module.ControlledHardwarePreflightInput(**values)

class TestHardwarePreflight(unittest.TestCase):
    def test_current_locked_chain_is_audit_ready_but_never_admissible(self):
        r = module.evaluate_controlled_hardware_preflight(baseline())
        self.assertEqual(r.state, "PREFLIGHT_READY_LOCKED")
        self.assertTrue(r.audit_passed)
        self.assertTrue(r.protocol_ready)
        self.assertFalse(r.independent_evidence_ready)
        self.assertTrue(r.unlock_eligible)
        self.assertFalse(r.hardware_test_admissible)
        self.assertTrue(r.explicit_human_authorization_required)
        self.assertTrue(r.write_locked)
        self.assertFalse(r.real_write_used)
        self.assertIn("INDEPENDENT_TRANSPORT_EVIDENCE_NOT_READY", r.blockers)
        self.assertIn("GLOBAL_WRITE_LOCK", r.blockers)

    def test_out_of_bounds_blocks_preflight(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(test_power_w=101))
        self.assertEqual(r.state, "PREFLIGHT_BLOCKED_LOCKED")
        self.assertFalse(r.audit_passed)
        self.assertIn("CONTROLLED_TEST_BOUNDS_NOT_READY", r.blockers)

    def test_missing_zero_request_blocks_preflight(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(zero_request_prepared=False))
        self.assertFalse(r.audit_passed)
        self.assertIn("ZERO_RETURN_PROTOCOL_NOT_READY", r.blockers)

    def test_even_complete_evidence_never_unlocks_3b21(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(independent_evidence_complete=True, explicit_write_authorized=True))
        self.assertTrue(r.independent_evidence_ready)
        self.assertTrue(r.hardware_test_admissible)
        self.assertTrue(r.write_locked)
        self.assertFalse(r.reinjection_allowed)

if __name__ == "__main__":
    unittest.main()
