from custom_components.carpiquet_ems.automation_engine import (
    AutomationInput,
    STATE_DISABLED,
    STATE_DISCHARGE,
    STATE_IDLE,
    STATE_SAFE_HOLD,
    decide_automation,
)

def base(**changes):
    data = dict(
        enabled=True,
        grid_available=True,
        active_batteries=2,
        fallback_active=False,
        allow_fallback=True,
        grid_power_w=500,
        grid_target_w=0,
        deadband_w=20,
        requested_discharge_w=500,
        previous_state=STATE_IDLE,
        seconds_since_transition=20,
        minimum_hold_seconds=10,
    )
    data.update(changes)
    return AutomationInput(**data)

def test_disabled():
    d = decide_automation(base(enabled=False))
    assert d.state == STATE_DISABLED
    assert d.request_w == 0

def test_discharge():
    d = decide_automation(base())
    assert d.state == STATE_DISCHARGE
    assert d.request_w == 500

def test_idle_inside_deadband():
    d = decide_automation(base(grid_power_w=10))
    assert d.state == STATE_IDLE

def test_safe_hold_without_grid():
    d = decide_automation(base(grid_available=False))
    assert d.state == STATE_SAFE_HOLD
    assert not d.safety_ok

def test_safe_hold_without_battery():
    d = decide_automation(base(active_batteries=0))
    assert d.state == STATE_SAFE_HOLD

def test_fallback_can_be_blocked():
    d = decide_automation(base(fallback_active=True, allow_fallback=False))
    assert d.state == STATE_SAFE_HOLD

def test_minimum_hold_blocks_normal_transition():
    d = decide_automation(base(seconds_since_transition=2, minimum_hold_seconds=10))
    assert d.state == STATE_IDLE
    assert d.reason == "minimum_hold"
