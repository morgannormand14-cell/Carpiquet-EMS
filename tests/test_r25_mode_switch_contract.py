"""R25 mode-switch integration contract checks (no hardware)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"


def test_mode_switch_is_wired_to_coordinator():
    switch = (ROOT / "switch.py").read_text(encoding="utf-8")
    coordinator = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    assert "R25RealCycleSwitch(coordinator, entry)" in switch
    assert "async_set_r25_cycle_mode(True)" in switch
    assert "async_set_r25_cycle_mode(False)" in switch
    assert "self._r25_cycle_mode = \"Simulation\"" in coordinator
    assert "self._r25_cycle_mode = \"Cycle réel\"" in coordinator
    assert "DynamicControlSession(controller)" in coordinator
    assert "await self._r25_session.apply(" in coordinator
    assert "await session.close()" in coordinator


def test_no_r24_executor_replacement():
    coordinator = (ROOT / "coordinator.py").read_text(encoding="utf-8")
    assert "execute_single_solarflow_test(" in coordinator
    assert "async_execute_real_controlled_test" in coordinator
