"""Read-only R25 command/telemetry correlation.

Transport acknowledgement is never equivalent to physical pack confirmation.
No device IO or command publication is performed by this module.
"""
from __future__ import annotations

from dataclasses import dataclass

from .transition_confirmation_tracker import (
    PendingTransition, TransitionConfirmation, evaluate_confirmation, start_tracking,
)

TRANSPORTS = {
    "hyper_2000": frozenset(("LOCAL_MQTT", "CLOUD_MQTT")),
    "solarflow_2400_pro": frozenset(("ZenSDK",)),
}


@dataclass(frozen=True)
class CorrelationResult:
    state: str
    confirmed: bool
    fault: bool
    reason: str
    command_id: str | None


def correlate_transition(*, system_id: str, transport: str, action: str,
                         command_id: str | None, dispatched: bool,
                         sent_at: float | None, transport_accepted: bool,
                         now: float, telemetry_at: float | None,
                         observed_state: str | None, observed_soc: float | None,
                         minimum_soc: float | None, observed_power_w: float | None = None,
                         timeout_s: float = 30.0) -> CorrelationResult:
    """Evaluate only evidence tied to an actually dispatched command.

    A successful HTTP response/MQTT publish alone cannot confirm a pack transition.
    Missing identity, invalid transport, or missing dispatch evidence fails closed.
    """
    if transport not in TRANSPORTS.get(system_id, ()):
        return CorrelationResult("NOT_TRACKED", False, False, "transport_not_qualified", command_id)
    if not dispatched or sent_at is None or not command_id:
        return CorrelationResult("NOT_TRACKED", False, False, "no_proven_dispatch", command_id)
    try:
        pending: PendingTransition = start_tracking(
            system_id=system_id, transport=transport, action=action,
            sent_at=sent_at, timeout_s=timeout_s, command_id=command_id,
        )
    except (ValueError, TypeError, OverflowError):
        return CorrelationResult("FAULT", False, True, "invalid_dispatch_evidence", command_id)
    if not transport_accepted:
        return CorrelationResult("PENDING", False, False, "transport_not_acknowledged", command_id)
    try:
        result: TransitionConfirmation = evaluate_confirmation(
            pending, now=now, telemetry_at=telemetry_at,
            observed_state=observed_state, observed_soc=observed_soc,
            minimum_soc=minimum_soc, observed_power_w=observed_power_w,
        )
    except (ValueError, TypeError, OverflowError):
        return CorrelationResult("FAULT", False, True, "invalid_telemetry_evidence", command_id)
    return CorrelationResult(result.state, result.confirmed, result.fault,
                             result.reason, result.command_id)
