from __future__ import annotations

from dataclasses import dataclass

STATE_DISABLED = "disabled"
STATE_SAFE_HOLD = "safe_hold"
STATE_IDLE = "idle"
STATE_DISCHARGE = "discharge"

REASON_DISABLED = "automation_disabled"
REASON_GRID_UNAVAILABLE = "grid_unavailable"
REASON_NO_BATTERY = "no_battery_available"
REASON_FALLBACK_BLOCKED = "fallback_blocked"
REASON_MIN_HOLD = "minimum_hold"
REASON_DEADBAND = "inside_deadband"
REASON_DISCHARGE = "grid_import_above_target"

POLICY = "grid_zero_discharge_v1"

@dataclass(frozen=True)
class AutomationInput:
    enabled: bool
    grid_available: bool
    active_batteries: int
    fallback_active: bool
    allow_fallback: bool
    grid_power_w: float
    grid_target_w: float
    deadband_w: float
    requested_discharge_w: float
    previous_state: str
    seconds_since_transition: float
    minimum_hold_seconds: float

@dataclass(frozen=True)
class AutomationDecision:
    state: str
    reason: str
    request_w: float
    safety_ok: bool
    transition: bool
    hold_remaining_seconds: float

def decide_automation(data: AutomationInput) -> AutomationDecision:
    if not data.enabled:
        desired = STATE_DISABLED
        reason = REASON_DISABLED
        request = 0.0
        safety_ok = True
    elif not data.grid_available:
        desired = STATE_SAFE_HOLD
        reason = REASON_GRID_UNAVAILABLE
        request = 0.0
        safety_ok = False
    elif data.active_batteries <= 0:
        desired = STATE_SAFE_HOLD
        reason = REASON_NO_BATTERY
        request = 0.0
        safety_ok = False
    elif data.fallback_active and not data.allow_fallback:
        desired = STATE_SAFE_HOLD
        reason = REASON_FALLBACK_BLOCKED
        request = 0.0
        safety_ok = False
    elif data.grid_power_w - data.grid_target_w > data.deadband_w:
        desired = STATE_DISCHARGE
        reason = REASON_DISCHARGE
        request = max(0.0, data.requested_discharge_w)
        safety_ok = True
    else:
        desired = STATE_IDLE
        reason = REASON_DEADBAND
        request = 0.0
        safety_ok = True

    transition = desired != data.previous_state
    hold_remaining = max(
        0.0,
        float(data.minimum_hold_seconds) - float(data.seconds_since_transition),
    )

    # A safety state always bypasses hold. Normal state changes are debounced.
    if (
        transition
        and desired not in (STATE_SAFE_HOLD, STATE_DISABLED)
        and data.previous_state not in ("", STATE_SAFE_HOLD, STATE_DISABLED)
        and hold_remaining > 0
    ):
        return AutomationDecision(
            state=data.previous_state,
            reason=REASON_MIN_HOLD,
            request_w=0.0 if data.previous_state == STATE_IDLE else request,
            safety_ok=safety_ok,
            transition=False,
            hold_remaining_seconds=round(hold_remaining, 1),
        )

    return AutomationDecision(
        state=desired,
        reason=reason,
        request_w=round(request, 1),
        safety_ok=safety_ok,
        transition=transition,
        hold_remaining_seconds=0.0,
    )
