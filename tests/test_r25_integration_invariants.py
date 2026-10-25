"""Static integration invariants for R25 and R24 hardware isolation."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems"
coordinator = (ROOT / "coordinator.py").read_text(encoding="utf-8")
session = (ROOT / "dynamic_control_session.py").read_text(encoding="utf-8")
executor = (ROOT / "controlled_real_test_executor.py").read_text(encoding="utf-8")

def test_r25_update_and_stop_share_lock():
    tree = ast.parse(coordinator)
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.AsyncWith)]
    def has_update_lock(node):
        return any(isinstance(i.context_expr, ast.Attribute) and
                   i.context_expr.attr == "_r25_update_lock" for i in node.items)
    blocks = [ast.get_source_segment(coordinator, n) or "" for n in nodes if has_update_lock(n)]
    assert any("self._r25_session.apply(" in b for b in blocks)
    assert any("session.close()" in b for b in blocks)
    assert any("previous.close()" in b for b in blocks)

def test_real_cycle_requires_fresh_safety_and_transport():
    assert "command_decision.safety_ok" in coordinator
    assert "grid_source_fresh and solar_command_sources_ok" in coordinator
    assert "self._solarflow_local_probe.qualified" in coordinator

def test_r24_one_shot_still_has_zero_recovery():
    assert "async def _restore_zero(" in executor
    assert "ZERO_ATTEMPTS" in executor
    assert "zero_verified" in executor

def test_r25_session_uses_watchdog():
    assert "DynamicWatchdog(" in session
    assert "await self._watchdog.close()" in session
