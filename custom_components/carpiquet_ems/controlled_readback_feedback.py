from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_READBACK_READY_LOCKED = "READBACK_READY_LOCKED"
STATE_READBACK_FAILED_LOCKED = "READBACK_FAILED_LOCKED"

REASON_READBACK_NOT_CONFIRMED = "REAL_READBACK_NOT_CONFIRMED"
REASON_READBACK_FAILED = "REAL_READBACK_FAILED"
REASON_NO_POST_PROOF = "NO_TRANSPORT_POST_PROOF"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledReadbackFeedbackInput:
    """Read-only 3B-10 facts accepted by the 3B-11 adapter."""

    readback_state: str
    read_confirmed: bool
    report_available: bool
    observed_output_w: float | None
    http_status: int | None


@dataclass(frozen=True)
class ControlledReadbackFeedback:
    """3B-11 one-way adapter from real GET readback toward 3B-9.

    The adapter deliberately cannot manufacture POST confirmation. It only
    forwards a confirmed report observation. Writes and reinjection stay
    hard-locked.
    """

    state: str
    blockers: tuple[str, ...]
    report_forwarded: bool
    report_available: bool
    observed_output_w: float | None
    read_http_status: int | None
    transport_result_available: bool
    transport_http_status: int | None
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def evaluate_controlled_readback_feedback(
    context: ControlledReadbackFeedbackInput,
) -> ControlledReadbackFeedback:
    blockers: list[str] = []
    confirmed = bool(
        context.readback_state == "READ_CONFIRMED_LOCKED"
        and context.read_confirmed
        and context.report_available
        and context.observed_output_w is not None
        and context.http_status == 200
    )

    if confirmed:
        state = STATE_READBACK_READY_LOCKED
        report_forwarded = True
    else:
        state = (
            STATE_READBACK_FAILED_LOCKED
            if context.readback_state == "READ_FAILED_LOCKED"
            else STATE_LOCKED
        )
        report_forwarded = False
        blockers.append(
            REASON_READBACK_FAILED
            if context.readback_state == "READ_FAILED_LOCKED"
            else REASON_READBACK_NOT_CONFIRMED
        )

    # A GET 200 is evidence for the report read only. It must never be reused
    # as proof that a POST /properties/write happened.
    blockers.extend((REASON_NO_POST_PROOF, REASON_GLOBAL_LOCK))

    return ControlledReadbackFeedback(
        state=state,
        blockers=tuple(blockers),
        report_forwarded=report_forwarded,
        report_available=report_forwarded,
        observed_output_w=context.observed_output_w if report_forwarded else None,
        read_http_status=context.http_status,
        transport_result_available=False,
        transport_http_status=None,
        write_locked=True,
        reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
