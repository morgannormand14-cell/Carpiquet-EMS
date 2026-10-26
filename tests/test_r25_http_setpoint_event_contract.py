"""Static regression: actual HTTP POST evidence is distinct from pack transition."""
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] /
          "custom_components/carpiquet_ems/dynamic_http_executor.py").read_text()


def test_event_is_created_at_post_not_at_preparation():
    assert "class HttpSetpointEvent:" in SOURCE
    assert "command_id = uuid4().hex" in SOURCE
    assert "sent_at = monotonic()" in SOURCE
    assert "status = await _post(session, self.write_target, self._body(float(watts)))" in SOURCE
    assert "200 <= status < 300" in SOURCE


def test_setpoint_evidence_does_not_claim_pack_transition():
    assert "NOT a physical pack transition" in SOURCE
    assert "self._last_setpoint_event" in SOURCE
    assert "pack_transition_confirmed" not in SOURCE


def test_coordinator_surfaces_http_event_without_pack_confirmation():
    root = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
    session = (root / "dynamic_control_session.py").read_text()
    coordinator = (root / "coordinator.py").read_text()
    assert "def last_setpoint_event(self):" in session
    assert "return self.executor.last_setpoint_event" in session
    assert '"r25_http_post_event": {' in coordinator
    assert '"transport_accepted": bool(http_setpoint_event and http_setpoint_event.transport_accepted)' in coordinator
    assert '"pack_transition_confirmed": False' in coordinator
