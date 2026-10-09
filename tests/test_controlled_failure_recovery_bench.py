"""3B-19 locked failure bench regression tests (without HA or network)."""
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems" / "controlled_failure_recovery_bench.py"
spec = importlib.util.spec_from_file_location("controlled_failure_recovery_bench", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class TestLockedRecovery(unittest.TestCase):
    def test_all_scenarios_locked_and_unconfirmed(self):
        result = module.run_locked_failure_recovery_bench()
        self.assertEqual(result.total_count, 9)
        self.assertEqual(result.passed_count, 9)
        self.assertTrue(result.all_passed)
        self.assertEqual(result.state, "BENCH_PASSED_LOCKED")
        self.assertTrue(result.zero_return_required)
        self.assertFalse(result.zero_return_confirmed)
        self.assertTrue(result.write_locked)
        self.assertFalse(result.reinjection_allowed)
        self.assertFalse(result.real_transport_used)

    def test_every_failure_demands_zero_without_fake_confirmation(self):
        for scenario in module.FAILURE_SCENARIOS:
            with self.subTest(scenario=scenario):
                decision = module.evaluate_locked_failure(scenario)
                self.assertEqual(decision.state, "RECOVERY_REQUIRED_LOCKED")
                self.assertTrue(decision.zero_return_required)
                self.assertFalse(decision.zero_return_command_sent)
                self.assertFalse(decision.zero_return_confirmed)
                self.assertTrue(decision.relock_required)
                self.assertIn("GLOBAL_WRITE_LOCK", decision.blockers)

    def test_unknown_scenario_fails_closed(self):
        decision = module.evaluate_locked_failure("UNEXPECTED")
        self.assertFalse(decision.passed)
        self.assertEqual(decision.state, "INVALID_SCENARIO_LOCKED")
        self.assertFalse(decision.zero_return_confirmed)
        self.assertTrue(decision.write_locked)
        self.assertFalse(decision.real_transport_used)

if __name__ == "__main__":
    unittest.main()
