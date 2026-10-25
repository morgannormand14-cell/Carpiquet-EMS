"""Read-only eligibility supervision ahead of the validated allocation algorithm.

Zendure-HA packState: 0 standby, 1 charging, 2 discharging, 3 off.
This module never sends a device command or changes the allocator.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PackEligibility:
    state: str
    eligible: bool
    needs_discharge_transition: bool
    needs_standby_transition: bool
    reason: str


def evaluate_pack(raw_state: object, soc: float | None, min_soc: float | None) -> PackEligibility:
    """Conservatively decide whether a pack may enter the discharge allocation.

    Standby above minimum is a *candidate*, not eligible until discharge is
    confirmed. No physical transition is performed here.
    """
    try:
        raw = int(raw_state)
        if str(raw_state).strip() not in (str(raw), str(float(raw))):
            raise ValueError("non-integral pack state")
    except (TypeError, ValueError, OverflowError):
        return PackEligibility("unknown", False, False, False, "pack_state_unknown")
    names = {0: "standby", 1: "charging", 2: "discharging", 3: "off"}
    state = names.get(raw, "unknown")
    if state == "unknown":
        return PackEligibility(state, False, False, False, "pack_state_unknown")
    if state == "off":
        return PackEligibility(state, False, False, False, "pack_off")
    if state == "charging":
        return PackEligibility(state, False, False, False, "pack_charging")
    try:
        soc_value, minimum = float(soc), float(min_soc)
        if not (0 <= soc_value <= 100 and 0 <= minimum <= 100):
            raise ValueError("out-of-range soc")
    except (TypeError, ValueError, OverflowError):
        return PackEligibility(state, False, False, False, "soc_unavailable")
    if soc_value <= minimum:
        return PackEligibility(state, False, False, state == "discharging", "soc_minimum")
    if state == "standby":
        return PackEligibility(state, False, True, False, "await_discharge_confirmation")
    return PackEligibility(state, True, False, False, "discharging_available")
