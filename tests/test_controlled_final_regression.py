"""3B-20 final locked non-regression tests."""
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems" / "controlled_final_regression.py"
spec = importlib.util.spec_from_file_location("controlled_final_regression", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def baseline(**overrides):
    values = dict(
        coherence_state="COHERENCE_READY_LOCKED",
        safety_boundary_coherent=True, execution_admissible=False,
        coherence_write_locked=True, coherence_reinjection_allowed=False,
        identity_state="IDENTITY_READY_LOCKED", identity_ready=True,
        independent_transport_proof_verified=False, readback_causally_bound=False,
        identity_write_locked=True, identity_reinjection_allowed=False,
        recovery_state="BENCH_PASSED_LOCKED", recovery_all_passed=True,
        recovery_zero_required=True, recovery_zero_confirmed=False,
        recovery_write_locked=True, recovery_reinjection_allowed=False,
        recovery_real_transport_used=False, loop_success_passed=True,
        loop_failure_passed=True, loop_degraded_all_passed=True,
        loop_edge_cases_passed=True,
    )
    values.update(overrides)
    return module.ControlledFinalRegressionInput(**values)

class TestFinalRegression(unittest.TestCase):
    def test_locked_chain_passes_without_authorizing_hardware(self):
        result = module.evaluate_controlled_final_regression(baseline())
        self.assertEqual(result.state, "REGRESSION_PASSED_LOCKED")
        self.assertTrue(result.regression_passed)
        self.assertFalse(result.evidence_complete)
        self.assertFalse(result.hardware_test_admissible)
        self.assertTrue(result.write_locked)
        self.assertFalse(result.reinjection_allowed)
        self.assertFalse(result.real_write_used)
        self.assertIn("INDEPENDENT_EVIDENCE_INCOMPLETE", result.blockers)
        self.assertIn("GLOBAL_WRITE_LOCK", result.blockers)

    def test_safety_regression_fails_closed(self):
        result = module.evaluate_controlled_final_regression(baseline(coherence_write_locked=False))
        self.assertEqual(result.state, "REGRESSION_FAILED_LOCKED")
        self.assertFalse(result.regression_passed)
        self.assertFalse(result.hardware_test_admissible)
        self.assertTrue(result.write_locked)

    def test_simulation_regression_fails_closed(self):
        result = module.evaluate_controlled_final_regression(baseline(loop_edge_cases_passed=False))
        self.assertEqual(result.state, "REGRESSION_FAILED_LOCKED")
        self.assertIn("SIMULATION_REGRESSION", result.blockers)

    def test_even_complete_evidence_does_not_unlock_3b20(self):
        result = module.evaluate_controlled_final_regression(baseline(
            independent_transport_proof_verified=True, readback_causally_bound=True))
        self.assertTrue(result.evidence_complete)
        self.assertFalse(result.hardware_test_admissible)
        self.assertTrue(result.write_locked)
        self.assertFalse(result.real_write_used)

if __name__ == "__main__":
    unittest.main()
