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
        test_power_w=177.0, power_limit_w=200.0, duration_seconds=5.0, single_device_only=True,
        local_http_only=True, watchdog_required=True, verification_required=True,
        zero_return_required=True, zero_on_failure_required=True,
        relock_required=True, test_request_prepared=True, zero_request_prepared=True,
        report_target_ready=True, test_armed=True, solarflow_selected=True,
        local_http_qualified=True, explicit_write_authorized=False,
    )
    values.update(overrides)
    return module.ControlledHardwarePreflightInput(**values)

class TestHardwarePreflight(unittest.TestCase):
    def test_current_locked_chain_is_unlock_eligible_but_not_authorized(self):
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
        self.assertIn("GLOBAL_WRITE_LOCK", r.blockers)

    def test_frozen_ems_setpoint_below_limit_is_eligible(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(test_power_w=177, power_limit_w=200))
        self.assertTrue(r.audit_passed)
        self.assertTrue(r.unlock_eligible)
        self.assertNotIn("POWER_ABOVE_TEST_LIMIT", r.blockers)

    def test_frozen_ems_setpoint_above_limit_is_refused(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(test_power_w=177, power_limit_w=100))
        self.assertEqual(r.state, "PREFLIGHT_BLOCKED_LOCKED")
        self.assertFalse(r.audit_passed)
        self.assertFalse(r.unlock_eligible)
        self.assertIn("POWER_ABOVE_TEST_LIMIT", r.blockers)
        self.assertIn("GLOBAL_WRITE_LOCK", r.blockers)

    def test_missing_frozen_ems_setpoint_blocks_preflight(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(test_power_w=0, power_limit_w=200))
        self.assertFalse(r.audit_passed)
        self.assertIn("EMS_SETPOINT_NOT_FROZEN", r.blockers)

    def test_power_limit_accepts_full_configured_range(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(test_power_w=2400, power_limit_w=2400))
        self.assertTrue(r.audit_passed)
        self.assertTrue(r.unlock_eligible)

    def test_duration_accepts_zero_and_six_hundred_seconds(self):
        self.assertTrue(module.evaluate_controlled_hardware_preflight(baseline(duration_seconds=0)).audit_passed)
        self.assertTrue(module.evaluate_controlled_hardware_preflight(baseline(duration_seconds=600)).audit_passed)

    def test_duration_above_six_hundred_seconds_fails_closed(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(duration_seconds=601))
        self.assertFalse(r.audit_passed)
        self.assertIn("CONTROLLED_TEST_BOUNDS_NOT_READY", r.blockers)

    def test_duration_accepts_ten_minutes_and_rejects_above(self):
        ok = module.evaluate_controlled_hardware_preflight(baseline(duration_seconds=600))
        too_long = module.evaluate_controlled_hardware_preflight(baseline(duration_seconds=601))
        zero = module.evaluate_controlled_hardware_preflight(baseline(duration_seconds=0))
        self.assertTrue(ok.audit_passed)
        self.assertFalse(too_long.audit_passed)
        self.assertFalse(zero.audit_passed)

    def test_missing_zero_request_blocks_preflight(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(zero_request_prepared=False))
        self.assertFalse(r.audit_passed)
        self.assertIn("ZERO_RETURN_PROTOCOL_NOT_READY", r.blockers)

    def test_explicit_authorization_admits_only_after_preflight(self):
        r = module.evaluate_controlled_hardware_preflight(baseline(independent_evidence_complete=True, explicit_write_authorized=True))
        self.assertTrue(r.independent_evidence_ready)
        self.assertTrue(r.hardware_test_admissible)
        self.assertTrue(r.write_locked)
        self.assertFalse(r.reinjection_allowed)

if __name__ == "__main__":
    unittest.main()
