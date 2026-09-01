from datetime import datetime, timedelta, timezone

from custom_components.carpiquet_ems.safety_state_machine import (
    SafetyStateMachine,
    STATE_SAFE_IDLE,
    STATE_RECOVERY,
    STATE_SHADOW_ACTIVE,
    STATE_HOLD,
    STATE_FAULT,
    STATE_ARMED_LOCKED,
)


def test_shadow_requires_recovery_before_active():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sm = SafetyStateMachine(hold_to_fault_seconds=30, recovery_seconds=10)
    sm.reset(t0)
    assert sm.update("Simulation", True, "OK", "ok", t0).state == STATE_SAFE_IDLE
    assert sm.update("Shadow", True, "OK", "ok", t0).state == STATE_RECOVERY
    assert sm.update("Shadow", True, "OK", "ok", t0 + timedelta(seconds=9)).shadow_authorized is False
    snap = sm.update("Shadow", True, "OK", "ok", t0 + timedelta(seconds=10))
    assert snap.state == STATE_SHADOW_ACTIVE
    assert snap.shadow_authorized is True


def test_transient_fault_hold_then_recovery():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sm = SafetyStateMachine(30, 10)
    sm.reset(t0)
    sm.update("Shadow", True, "OK", "ok", t0)
    sm.update("Shadow", True, "OK", "ok", t0 + timedelta(seconds=10))
    hold = sm.update("Shadow", False, "GRID_UNAVAILABLE", "grid absent", t0 + timedelta(seconds=11))
    assert hold.state == STATE_HOLD
    assert hold.shadow_authorized is False
    recovery = sm.update("Shadow", True, "OK", "ok", t0 + timedelta(seconds=15))
    assert recovery.state == STATE_RECOVERY
    active = sm.update("Shadow", True, "OK", "ok", t0 + timedelta(seconds=25))
    assert active.state == STATE_SHADOW_ACTIVE


def test_persistent_fault_escalates():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sm = SafetyStateMachine(30, 10)
    sm.reset(t0)
    assert sm.update("Shadow", False, "GRID_STALE", "stale", t0).state == STATE_HOLD
    assert sm.update("Shadow", False, "GRID_STALE", "stale", t0 + timedelta(seconds=29)).state == STATE_HOLD
    fault = sm.update("Shadow", False, "GRID_STALE", "stale", t0 + timedelta(seconds=30))
    assert fault.state == STATE_FAULT
    assert fault.fault_count == 1


def test_armed_is_always_locked_state():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sm = SafetyStateMachine()
    snap = sm.update("Armed", True, "OK", "ok", t0)
    assert snap.state == STATE_ARMED_LOCKED
    assert snap.shadow_authorized is False
