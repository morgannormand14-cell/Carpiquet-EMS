"""R25 post-command confirmation tracker; pure, no device writes.

A command must have been explicitly dispatched before it can be confirmed.
Telemetry must be fresher than dispatch, and timeout latches a fault.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .transition_feedback import verify_transition


@dataclass(frozen=True)
class PendingTransition:
    system_id: str
    transport: str
    action: str
    sent_at: float
    deadline_at: float
    command_id: str


@dataclass(frozen=True)
class TransitionConfirmation:
    state: str
    confirmed: bool
    fault: bool
    reason: str
    command_id: str


def start_tracking(*, system_id: str, transport: str, action: str,
                   sent_at: float, timeout_s: float, command_id: str) -> PendingTransition:
    if not system_id or not transport or not command_id:
        raise ValueError("Missing command identity")
    if action not in ("request_discharge", "request_standby"):
        raise ValueError("Unsupported transition action")
    if not all(isfinite(float(v)) for v in (sent_at, timeout_s)) or not 0 < timeout_s <= 120:
        raise ValueError("Invalid dispatch time or confirmation timeout")
    return PendingTransition(system_id, transport, action, float(sent_at),
                             float(sent_at) + float(timeout_s), command_id)


def evaluate_confirmation(pending: PendingTransition, *, now: float,
                          telemetry_at: float | None, observed_state: str | None,
                          observed_soc: float | None, minimum_soc: float | None,
                          observed_power_w: float | None = None) -> TransitionConfirmation:
    if not isfinite(float(now)):
        return TransitionConfirmation("FAULT", False, True, "invalid_clock", pending.command_id)
    if now > pending.deadline_at:
        return TransitionConfirmation("FAULT", False, True, "confirmation_timeout", pending.command_id)
    if telemetry_at is None or not isfinite(float(telemetry_at)):
        return TransitionConfirmation("PENDING", False, False, "telemetry_timestamp_missing", pending.command_id)
    if telemetry_at <= pending.sent_at or telemetry_at > now:
        return TransitionConfirmation("PENDING", False, False, "telemetry_not_post_command", pending.command_id)
    feedback = verify_transition(
        pending.action, observed_state=observed_state, fresh=True,
        observed_soc=observed_soc, minimum_soc=minimum_soc,
        observed_power_w=observed_power_w,
    )
    return TransitionConfirmation(
        "CONFIRMED" if feedback.confirmed else "FAULT" if feedback.state == "BLOCKED" else "PENDING",
        feedback.confirmed, feedback.state == "BLOCKED", feedback.reason, pending.command_id,
    )
