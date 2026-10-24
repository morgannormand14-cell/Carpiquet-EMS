"""Safety-boundary tests for the 3B-21 real executor."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems" / "controlled_real_test_executor.py"
spec = importlib.util.spec_from_file_location("controlled_real_test_executor", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class TestRealExecutorBoundary(unittest.TestCase):
    def test_rejects_non_write_target_before_io(self):
        with self.assertRaises(ValueError):
            asyncio.run(module.execute_single_solarflow_test(
                None, test_target="http://device/properties/report",
                report_target="http://device/properties/report",
                test_body={"properties":{"outputLimit":50}}, zero_body={"properties":{"outputLimit":0}},
                power_w=50, duration_seconds=5))

    def test_rejects_out_of_bounds_before_io(self):
        with self.assertRaises(ValueError):
            asyncio.run(module.execute_single_solarflow_test(
                None, test_target="http://device/properties/write",
                report_target="http://device/properties/report",
                test_body={"properties":{"outputLimit":2401}}, zero_body={"properties":{"outputLimit":0}},
                power_w=2401, duration_seconds=5))

    def test_rejects_duration_above_ten_minutes_before_io(self):\n        with self.assertRaises(ValueError):\n            asyncio.run(module.execute_single_solarflow_test(\n                None, test_target="http://device/properties/write",\n                report_target="http://device/properties/report",\n                test_body={"properties":{"outputLimit":50}}, zero_body={"properties":{"outputLimit":0}},\n                power_w=50, duration_seconds=601))\n\n    def test_rejects_zero_duration_before_io(self):\n        with self.assertRaises(ValueError):\n            asyncio.run(module.execute_single_solarflow_test(\n                None, test_target="http://device/properties/write",\n                report_target="http://device/properties/report",\n                test_body={"properties":{"outputLimit":50}}, zero_body={"properties":{"outputLimit":0}},\n                power_w=50, duration_seconds=0))\n\n    def test_rejects_invalid_zero_body_before_io(self):
        with self.assertRaises(ValueError):
            asyncio.run(module.execute_single_solarflow_test(
                None, test_target="http://device/properties/write",
                report_target="http://device/properties/report",
                test_body={"properties":{"outputLimit":50}}, zero_body={"properties":{"outputLimit":1}},
                power_w=50, duration_seconds=5))

if __name__ == "__main__":
    unittest.main()
