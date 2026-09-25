from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_AUTHORIZED_LOCKED = "AUTHORIZED_LOCKED"
STATE_TEST_PREPARED = "TEST_PREPARED"
STATE_TEST_VERIFY_PENDING = "TEST_VERIFY_PENDING"
STATE_ZERO_RETURN_REQUIRED = "ZERO_RETURN_REQUIRED"
STATE_ZERO_VERIFY_PENDING = "ZERO_VERIFY_PENDING"
STATE_COMPLETE_LOCKED = "COMPLETE_LOCKED"
STATE_FAILED_LOCKED = "FAILED_LOCKED"

REASON_AUTHORIZATION_REQUIRED = "EXPLICIT_WRITE_AUTHORIZATION_REQUIRED"
REASON_SOLARFLOW_ONLY = "SOLARFLOW_ONLY"
REASON_LOCAL_HTTP_REQUIRED = "LOCAL_HTTP_REQUIRED"
REASON_GATE_NOT_READY = "CONTROLLED_TEST_GATE_NOT_READY"
REASON_VERIFICATION_NOT_READY = "VERIFICATION_PLAN_NOT_READY"
REASON_POST_NOT_CONFIRMED = "TEST_POST_NOT_CONFIRMED"
REASON_OUTPUT_NOT_CONFIRMED = "TEST_OUTPUT_NOT_CONFIRMED"
REASON_ZERO_POST_NOT_CONFIRMED = "ZERO_POST_NOT_CONFIRMED"
REASON_ZERO_NOT_CONFIRMED = "ZERO_OUTPUT_NOT_CONFIRMED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledTestSequenceInput:
    explicit_write_authorized: bool
    device: str
    selected_transport: str
    gate_ready: bool
    verification_ready: bool
    test_post_confirmed: bool = False
    test_output_confirmed: bool = False
    zero_post_confirmed: bool = False
    zero_output_confirmed: bool = False
    failure_detected: bool = False


@dataclass(frozen=True)
class ControlledTestSequenceDecision:
    state: str
    blockers: tuple[str, ...]
    test_write_requested: bool
    test_write_allowed: bool
    test_write_sent: bool
    verification_required: bool
    return_to_zero_required: bool
    zero_write_requested: bool
    zero_write_allowed: bool
    zero_write_sent: bool
    relock_required: bool
    evaluated_at: str


def evaluate_controlled_test_sequence(
    context: ControlledTestSequenceInput,
) -> ControlledTestSequenceDecision:
    """Model the Phase 3B test lifecycle without performing or allowing I/O.

    Step 2 is deliberately simulation-only. It models the future sequence through
    test verification, mandatory zero return, zero verification, and relock while
    GLOBAL_WRITE_LOCK remains authoritative.
    """
    blockers: list[str] = []
    if not context.explicit_write_authorized:
        blockers.append(REASON_AUTHORIZATION_REQUIRED)
    if context.device != "solarflow":
        blockers.append(REASON_SOLARFLOW_ONLY)
    if context.selected_transport != "LOCAL_HTTP":
        blockers.append(REASON_LOCAL_HTTP_REQUIRED)
    if not context.gate_ready:
        blockers.append(REASON_GATE_NOT_READY)
    if not context.verification_ready:
        blockers.append(REASON_VERIFICATION_NOT_READY)

    prerequisites_ready = not blockers

    if context.failure_detected:
        state = STATE_FAILED_LOCKED
    elif not context.explicit_write_authorized:
        state = STATE_LOCKED
    elif not prerequisites_ready:
        state = STATE_AUTHORIZED_LOCKED
    elif not context.test_post_confirmed:
        state = STATE_TEST_PREPARED
        blockers.append(REASON_POST_NOT_CONFIRMED)
    elif not context.test_output_confirmed:
        state = STATE_TEST_VERIFY_PENDING
        blockers.append(REASON_OUTPUT_NOT_CONFIRMED)
    elif not context.zero_post_confirmed:
        state = STATE_ZERO_RETURN_REQUIRED
        blockers.append(REASON_ZERO_POST_NOT_CONFIRMED)
    elif not context.zero_output_confirmed:
        state = STATE_ZERO_VERIFY_PENDING
        blockers.append(REASON_ZERO_NOT_CONFIRMED)
    else:
        state = STATE_COMPLETE_LOCKED

    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledTestSequenceDecision(
        state=state,
        blockers=tuple(blockers),
        test_write_requested=state in (STATE_TEST_PREPARED, STATE_TEST_VERIFY_PENDING),
        test_write_allowed=False,
        test_write_sent=False,
        verification_required=state in (
            STATE_TEST_PREPARED,
            STATE_TEST_VERIFY_PENDING,
            STATE_ZERO_RETURN_REQUIRED,
            STATE_ZERO_VERIFY_PENDING,
        ),
        return_to_zero_required=True,
        zero_write_requested=state in (STATE_ZERO_RETURN_REQUIRED, STATE_ZERO_VERIFY_PENDING),
        zero_write_allowed=False,
        zero_write_sent=False,
        relock_required=True,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
