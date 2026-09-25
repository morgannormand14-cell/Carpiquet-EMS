from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_TEST_READY_LOCKED = "TEST_READY_LOCKED"
STATE_TEST_VERIFY_LOCKED = "TEST_VERIFY_LOCKED"
STATE_ZERO_REQUIRED_LOCKED = "ZERO_REQUIRED_LOCKED"
STATE_ZERO_VERIFY_LOCKED = "ZERO_VERIFY_LOCKED"
STATE_COMPLETE_LOCKED = "COMPLETE_LOCKED"
STATE_FAILED_LOCKED = "FAILED_LOCKED"

REASON_SAFETY_NOT_READY = "EXECUTION_SAFETY_NOT_READY"
REASON_TEST_NOT_CONFIRMED = "TEST_POST_NOT_CONFIRMED"
REASON_TEST_OUTPUT_NOT_CONFIRMED = "TEST_OUTPUT_NOT_CONFIRMED"
REASON_ZERO_NOT_CONFIRMED = "ZERO_POST_NOT_CONFIRMED"
REASON_ZERO_OUTPUT_NOT_CONFIRMED = "ZERO_OUTPUT_NOT_CONFIRMED"
REASON_FAILURE = "FAILURE_DETECTED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledExecutionOrchestratorInput:
    """Observed inputs for the locked Phase 3B-7 orchestration model."""

    safety_state: str
    test_post_confirmed: bool = False
    test_output_confirmed: bool = False
    bounded_duration_elapsed: bool = False
    zero_post_confirmed: bool = False
    zero_output_confirmed: bool = False
    failure_detected: bool = False


@dataclass(frozen=True)
class ControlledExecutionOrchestratorDecision:
    """Data-only orchestration decision; never performs hardware I/O."""

    state: str
    blockers: tuple[str, ...]
    next_action: str
    test_post_requested: bool
    test_post_allowed: bool
    test_post_sent: bool
    report_verification_requested: bool
    wait_requested: bool
    zero_post_requested: bool
    zero_post_allowed: bool
    zero_post_sent: bool
    zero_verification_requested: bool
    relock_required: bool
    execution_allowed: bool
    command_sent: bool
    evaluated_at: str


def evaluate_controlled_execution_orchestrator(
    context: ControlledExecutionOrchestratorInput,
) -> ControlledExecutionOrchestratorDecision:
    """Model the complete controlled sequence while GLOBAL_WRITE_LOCK is active."""

    blockers: list[str] = []
    safety_ready = context.safety_state == "READY_LOCKED"

    if not safety_ready:
        blockers.append(REASON_SAFETY_NOT_READY)

    if context.failure_detected:
        state = STATE_FAILED_LOCKED
        next_action = "RETURN_ZERO_THEN_RELOCK"
        blockers.append(REASON_FAILURE)
    elif not safety_ready:
        state = STATE_LOCKED
        next_action = "WAIT_FOR_SAFETY_CONTRACT"
    elif not context.test_post_confirmed:
        state = STATE_TEST_READY_LOCKED
        next_action = "POST_TEST_OUTPUT_LIMIT"
        blockers.append(REASON_TEST_NOT_CONFIRMED)
    elif not context.test_output_confirmed:
        state = STATE_TEST_VERIFY_LOCKED
        next_action = "VERIFY_REPORT_OUTPUT"
        blockers.append(REASON_TEST_OUTPUT_NOT_CONFIRMED)
    elif not context.bounded_duration_elapsed:
        state = STATE_TEST_VERIFY_LOCKED
        next_action = "WAIT_BOUNDED_DURATION"
    elif not context.zero_post_confirmed:
        state = STATE_ZERO_REQUIRED_LOCKED
        next_action = "POST_ZERO_OUTPUT_LIMIT"
        blockers.append(REASON_ZERO_NOT_CONFIRMED)
    elif not context.zero_output_confirmed:
        state = STATE_ZERO_VERIFY_LOCKED
        next_action = "VERIFY_REPORT_ZERO"
        blockers.append(REASON_ZERO_OUTPUT_NOT_CONFIRMED)
    else:
        state = STATE_COMPLETE_LOCKED
        next_action = "RELOCK"

    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledExecutionOrchestratorDecision(
        state=state,
        blockers=tuple(blockers),
        next_action=next_action,
        test_post_requested=state == STATE_TEST_READY_LOCKED,
        test_post_allowed=False,
        test_post_sent=False,
        report_verification_requested=state == STATE_TEST_VERIFY_LOCKED,
        wait_requested=(state == STATE_TEST_VERIFY_LOCKED and next_action == "WAIT_BOUNDED_DURATION"),
        zero_post_requested=state in (STATE_ZERO_REQUIRED_LOCKED, STATE_FAILED_LOCKED),
        zero_post_allowed=False,
        zero_post_sent=False,
        zero_verification_requested=state == STATE_ZERO_VERIFY_LOCKED,
        relock_required=True,
        execution_allowed=False,
        command_sent=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
