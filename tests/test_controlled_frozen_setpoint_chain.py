"""3B frozen EMS setpoint identity regression; pure data, no HA/network."""
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems"
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod); return mod
prep_mod=load("controlled_local_http_execution"); bridge_mod=load("controlled_transport_bridge"); trace_mod=load("controlled_command_trace")
class FrozenSetpointChainTests(unittest.TestCase):
    def prepare(self, frozen):
        return prep_mod.prepare_controlled_local_http_execution(sequence_state="TEST_PREPARED",executor_prepared=True,target="http://device/properties/write",report_target="http://device/properties/report",envelope={"id":"req","sn":"serial","properties":{"outputLimit":999,"smartMode":1}},frozen_power_w=frozen)
    def test_frozen_setpoint_and_zero_are_preserved(self):
        p=self.prepare(177); self.assertEqual(p.test_request.json_body["properties"]["outputLimit"],177); self.assertEqual(p.zero_request.json_body["properties"]["outputLimit"],0); self.assertTrue(p.write_locked); self.assertFalse(p.test_request.execution_allowed)
    def test_bridge_preserves_exact_frozen_request(self):
        p=self.prepare(177); b=bridge_mod.prepare_controlled_transport_bridge(bridge_mod.ControlledTransportBridgeInput(orchestrator_state="TEST_READY_LOCKED",orchestrator_next_action="POST_TEST_OUTPUT_LIMIT",preparation_state=p.state,safety_state="READY_LOCKED",test_request_prepared=True,zero_request_prepared=True,test_target=p.test_request.target,test_body=p.test_request.json_body,zero_target=p.zero_request.target,zero_body=p.zero_request.json_body,report_target=p.report_target)); self.assertEqual(b.json_body["properties"]["outputLimit"],177); self.assertFalse(b.transport_call_allowed); self.assertFalse(b.transport_call_sent)
    def test_trace_identity_changes_with_frozen_setpoint(self):
        def trace(p): return trace_mod.evaluate_controlled_command_trace(trace_mod.ControlledCommandTraceInput(command_context_available=True,action="POST_TEST_OUTPUT_LIMIT",method="POST",target=p.test_request.target,json_body=p.test_request.json_body,request_prepared=True,transport_call_sent=False,transport_result_available=False,post_proof_available=False))
        a,b=trace(self.prepare(177)),trace(self.prepare(178)); self.assertTrue(a.identity_bound); self.assertNotEqual(a.request_fingerprint,b.request_fingerprint); self.assertTrue(a.write_locked); self.assertFalse(a.reinjection_allowed)
if __name__=="__main__": unittest.main()
