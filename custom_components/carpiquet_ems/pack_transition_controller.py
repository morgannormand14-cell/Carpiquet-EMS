"""R25 pack transition coordinator, strictly simulation-only.

Produces model-specific *intent*, not device writes. An adapter for physical
commands must be separately reviewed, authorized, and confirmation-gated.
"""
from __future__ import annotations

from dataclasses import dataclass

from .pack_state_supervisor import PackEligibility


@dataclass(frozen=True)
class TransitionIntent:
    system_id: str
    action: str
    reason: str
    simulated: bool = True


def plan_transition(system_id: str, eligibility: PackEligibility, *, discharge_needed: bool) -> TransitionIntent:
    """OFF/charging/unknown are never actively changed by the EMS."""
    if eligibility.needs_standby_transition:
        return TransitionIntent(system_id, "request_standby", "minimum_soc_reached")
    if eligibility.needs_discharge_transition and discharge_needed:
        return TransitionIntent(system_id, "request_discharge", "grid_import_requires_discharge")
    return TransitionIntent(system_id, "none", eligibility.reason)


def plan_transitions(packs: dict[str, PackEligibility], *, discharge_needed: bool) -> dict[str, dict]:
    return {
        system_id: {
            "action": (intent := plan_transition(system_id, eligibility, discharge_needed=discharge_needed)).action,
            "reason": intent.reason,
            "simulated": intent.simulated,
        }
        for system_id, eligibility in packs.items()
    }
