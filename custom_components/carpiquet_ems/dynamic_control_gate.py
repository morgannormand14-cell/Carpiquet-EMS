"""R25 dynamic control decision gate (pure logic; never performs hardware I/O).

The R24 one-shot executor remains the only hardware-writing path until the
continuous controller has an explicit enable/disable lifecycle and watchdog.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class DynamicGateDecision:
    state: str
    target_w: float
    should_write: bool
    must_stop: bool
    reason: str


def evaluate_dynamic_gate(
    *,
    requested_w: float,
    limit_w: float,
    local_mode: bool,
    transport_qualified: bool,
    soc_valid: bool,
    authorized: bool,
    previously_active: bool,
    last_command_w: float = 0.0,
    minimum_change_w: float = 10.0,
) -> DynamicGateDecision:
    """Evaluate one EMS cycle; output is advisory, never a write authorization.

    All callers must still enforce their own hardware interlocks. On a lost
    prerequisite, a previously active session requires a verified zero stop.
    """
    checks = (
        (local_mode, "NOT_LOCAL_MODE"),
        (transport_qualified, "TRANSPORT_UNQUALIFIED"),
        (soc_valid, "SOC_UNSAFE_OR_STALE"),
        (authorized, "AUTHORIZATION_REQUIRED"),
    )
    for ok, reason in checks:
        if not ok:
            return DynamicGateDecision(
                "STOP_REQUIRED" if previously_active else "LOCKED",
                0.0, False, previously_active, reason,
            )
    values = (requested_w, limit_w, last_command_w, minimum_change_w)
    if any(not isfinite(float(v)) for v in values):
        return DynamicGateDecision("STOP_REQUIRED" if previously_active else "LOCKED",
                                   0.0, False, previously_active, "INVALID_NUMBER")
    if not 0.0 < float(limit_w) <= 2400.0 or not 0.0 <= float(requested_w) <= float(limit_w):
        return DynamicGateDecision("STOP_REQUIRED" if previously_active else "LOCKED",
                                   0.0, False, previously_active, "POWER_OUT_OF_BOUNDS")
    if requested_w == 0:
        return DynamicGateDecision("STOP_REQUIRED" if previously_active else "IDLE",
                                   0.0, False, previously_active, "ZERO_REQUESTED")
    if minimum_change_w < 0:
        return DynamicGateDecision("LOCKED", 0.0, False, previously_active, "INVALID_DEADBAND")
    if previously_active and abs(float(requested_w) - float(last_command_w)) < minimum_change_w:
        return DynamicGateDecision("UNCHANGED", float(last_command_w), False, False, "DEADBAND")
    return DynamicGateDecision("READY_SHADOW", float(requested_w), False, False,
                               "R25_HARDWARE_WRITE_NOT_YET_ENABLED")
