"""Fail-closed 3B-18 contract tests; no Home Assistant or network required."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems" / "controlled_evidence_identity.py"
spec = importlib.util.spec_from_file_location("controlled_evidence_identity", MODULE)
import sys
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

FINGERPRINT = "a" * 64

class EvidenceIdentityTests(unittest.TestCase):
    def evaluate(self, **overrides):
        defaults = dict(
            trace_identity_bound=True, request_id="request-test",
            request_fingerprint=FINGERPRINT, observation_available=True,
            transport_receipt=None,
        )
        defaults.update(overrides)
        return mod.evaluate_controlled_evidence_identity(mod.ControlledEvidenceIdentityInput(**defaults))

    def test_without_receipt_identity_ready_but_never_verified(self):
        result = self.evaluate()
        self.assertEqual(result.state, "IDENTITY_READY_LOCKED")
        self.assertTrue(result.identity_ready)
        self.assertTrue(result.observation_available)
        self.assertFalse(result.independent_transport_proof_verified)
        self.assertFalse(result.readback_causally_bound)
        self.assertTrue(result.write_locked)
        self.assertFalse(result.reinjection_allowed)

    def test_forged_matching_receipt_not_authenticated(self):
        result = self.evaluate(transport_receipt={
            "request_id": "request-test", "request_fingerprint": FINGERPRINT,
            "authenticated": True, "http_status": 200,
        })
        self.assertTrue(result.receipt_identity_matches)
        self.assertFalse(result.receipt_authenticated)
        self.assertFalse(result.independent_transport_proof_verified)

    def test_mismatched_receipt_is_rejected(self):
        result = self.evaluate(transport_receipt={
            "request_id": "another-request", "request_fingerprint": FINGERPRINT,
        })
        self.assertFalse(result.receipt_identity_matches)
        self.assertIn("TRANSPORT_RECEIPT_IDENTITY_MISMATCH", result.blockers)

    def test_invalid_identity_cannot_bind(self):
        result = self.evaluate(request_fingerprint="not-a-sha256")
        self.assertFalse(result.identity_ready)
        self.assertEqual(result.state, "LOCKED")

    def test_get_observation_does_not_prove_post(self):
        result = self.evaluate(observation_available=True)
        self.assertFalse(result.receipt_present)
        self.assertFalse(result.independent_transport_proof_verified)
        self.assertIn("GLOBAL_WRITE_LOCK", result.blockers)

if __name__ == "__main__":
    unittest.main()
