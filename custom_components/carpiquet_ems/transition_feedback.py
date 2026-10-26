"""Fail-closed readback verification for R25 transition intents.

This module does not send commands. It only evaluates fresh device telemetry.
A successful publish/HTTP response is NOT proof of a physical transition.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TransitionFeedback:
    state: str
    confirmed: bool
    reason: str


def verify_transition(
    action: str, *, observed_state: str | None, fresh: bool,
    observed_soc: float | None, minimum_soc: float | None,
    observed_power_w: float | None = None,
) -> TransitionFeedback:
    if action not in ("request_discharge", "request_standby"):
        return TransitionFeedback("BLOCKED", False, "unsupported_action")
    if not fresh:
        return TransitionFeedback("PENDING", False, "telemetry_stale")
    if observed_state not in ("standby", "charging", "discharging", "off"):
        return TransitionFeedback("PENDING", False, "pack_state_unknown")
    if observed_state in ("charging", "off"):
        return TransitionFeedback("BLOCKED", False, "pack_not_controllable")
    try:
        soc = float(observed_soc)
        reserve = float(minimum_soc)
        if not all(map(isfinite, (soc, reserve))) or not (0 <= reserve <= 100 and 0 <= soc <= 100):
            raise ValueError("invalid SOC")
    except (ValueError, TypeError, OverflowError):
        return TransitionFeedback("PENDING", False, "soc_unavailable")
    if action == "request_discharge":
        if soc <= reserve:
            return TransitionFeedback("BLOCKED", False, "soc_minimum")
        if observed_state == "discharging":
            return TransitionFeedback("CONFIRMED", True, "discharge_state_confirmed")
        return TransitionFeedback("PENDING", False, "awaiting_discharge_state")
    if observed_state != "standby":
        return TransitionFeedback("PENDING", False, "awaiting_standby_state")
    try:
        power = float(observed_power_w)
    except (TypeError, ValueError, OverflowError):
        return TransitionFeedback("PENDING", False, "output_unavailable")
    if not isfinite(power) or abs(power) > 1.0:
        return TransitionFeedback("PENDING", False, "output_not_zero")
    return TransitionFeedback("CONFIRMED", True, "standby_and_zero_confirmed")
