"""R25 immutable transport evidence; never infers pack transition confirmation.

Only the actual transport executor may construct dispatched evidence.
Prepared commands and readback-only observations remain unproven.
No network I/O or device write is performed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .r25_command_correlation import CorrelationResult, correlate_transition


@dataclass(frozen=True)
class TransportEvidence:
    system_id: str
    transport: str
    action: str
    command_id: str | None = None
    dispatched: bool = False
    sent_at: float | None = None
    transport_accepted: bool = False


def correlate_evidence(evidence: TransportEvidence, *, now: float,
                       telemetry_at: float | None, observed_state: str | None,
                       observed_soc: float | None, minimum_soc: float | None,
                       observed_power_w: float | None = None,
                       timeout_s: float = 30.0) -> CorrelationResult:
    """Fail closed when dispatch or telemetry evidence is absent."""
    return correlate_transition(
        system_id=evidence.system_id, transport=evidence.transport,
        action=evidence.action, command_id=evidence.command_id,
        dispatched=evidence.dispatched, sent_at=evidence.sent_at,
        transport_accepted=evidence.transport_accepted, now=now,
        telemetry_at=telemetry_at, observed_state=observed_state,
        observed_soc=observed_soc, minimum_soc=minimum_soc,
        observed_power_w=observed_power_w, timeout_s=timeout_s,
    )


def unproven_transport_evidence(*, system_id: str, transport: str,
                                action: str) -> TransportEvidence:
    """Used for command preparation and observations, never a dispatch proof."""
    return TransportEvidence(system_id=system_id, transport=transport, action=action)


def dispatched_transport_evidence(*, system_id: str, transport: str,
                                  action: str, command_id: str,
                                  sent_at: float, accepted: bool) -> TransportEvidence:
    """Explicit dispatch proof; call only after an actual transport attempt.

    Transport acknowledgement is not a physical transition confirmation.
    """
    if not command_id or not isinstance(command_id, str):
        raise ValueError("Missing command identifier")
    if not isfinite(float(sent_at)):
        raise ValueError("Invalid dispatch timestamp")
    return TransportEvidence(system_id=system_id, transport=transport,
                             action=action, command_id=command_id,
                             dispatched=True, sent_at=float(sent_at),
                             transport_accepted=bool(accepted))
