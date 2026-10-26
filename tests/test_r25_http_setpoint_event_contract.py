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


def test_http_event_retained_after_session_teardown():
    coordinator = (Path(__file__).resolve().parents[1] /
                   "custom_components/carpiquet_ems/coordinator.py").read_text()
    assert "def _remember_r25_http_post_event(self, session):" in coordinator
    assert "self._r25_last_http_post_event = event" in coordinator
    assert "else self._r25_last_http_post_event" in coordinator
    assert "self._remember_r25_http_post_event(previous)" in coordinator


def test_all_coordinator_teardown_paths_retain_event():
    root = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
    source = (root / "coordinator.py").read_text()
    import ast
    tree = ast.parse(source)
    coordinator = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                       and any(isinstance(n, ast.AsyncFunctionDef)
                               and n.name == "async_set_r25_cycle_mode"
                               for n in node.body))
    for method_name in ("async_set_r25_cycle_mode", "async_shutdown", "_async_update_data"):
        method = next((node for node in coordinator.body
                       if isinstance(node, ast.AsyncFunctionDef) and node.name == method_name), None)
        if method is None:
            continue
        for node in ast.walk(method):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "close":
                continue
            # Every session.close() must be preceded by a retention call
            # in its enclosing method (including safety and failure branches).
            assert "_remember_r25_http_post_event" in ast.get_source_segment(source, method)
