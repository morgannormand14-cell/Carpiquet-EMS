from __future__ import annotations
from dataclasses import dataclass

STATE_DISABLED = "disabled"
STATE_SAFE_HOLD = "safe_hold"
STATE_IDLE = "idle"
STATE_DISCHARGE = "discharge"

POLICY = "grid_zero_bidirectional_v1"

DISPLAY_STATE = {
    STATE_DISABLED: "Désactivé",
    STATE_SAFE_HOLD: "Maintien de sécurité",
    STATE_IDLE: "Veille",
    STATE_DISCHARGE: "Décharge",
}

DISPLAY_REASON = {
    "automation_disabled": "Automatisation désactivée",
    "grid_unavailable": "Compteur réseau indisponible",
    "no_battery_available": "Aucune batterie disponible",
    "fallback_blocked": "Mode secours interdit",
    "minimum_hold": "Temporisation minimale",
    "inside_deadband": "Dans la bande morte",
    "grid_import_above_target": "Import réseau au-dessus de la cible",
}

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
        desired, reason, request, safety_ok = STATE_DISABLED, "automation_disabled", 0.0, True
    elif not data.grid_available:
        desired, reason, request, safety_ok = STATE_SAFE_HOLD, "grid_unavailable", 0.0, False
    elif data.active_batteries <= 0:
        desired, reason, request, safety_ok = STATE_SAFE_HOLD, "no_battery_available", 0.0, False
    elif data.fallback_active and not data.allow_fallback:
        desired, reason, request, safety_ok = STATE_SAFE_HOLD, "fallback_blocked", 0.0, False
    elif data.grid_power_w - data.grid_target_w > data.deadband_w:
        desired, reason, request, safety_ok = STATE_DISCHARGE, "grid_import_above_target", max(0.0, data.requested_discharge_w), True
    else:
        desired, reason, request, safety_ok = STATE_IDLE, "inside_deadband", 0.0, True

    transition = desired != data.previous_state
    hold_remaining = max(0.0, float(data.minimum_hold_seconds)-float(data.seconds_since_transition))
    if transition and desired not in (STATE_SAFE_HOLD, STATE_DISABLED) and data.previous_state not in ("", STATE_SAFE_HOLD, STATE_DISABLED) and hold_remaining > 0:
        return AutomationDecision(data.previous_state, "minimum_hold", 0.0 if data.previous_state == STATE_IDLE else request, safety_ok, False, round(hold_remaining,1))

    return AutomationDecision(desired, reason, round(request,1), safety_ok, transition, 0.0)
