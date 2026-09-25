from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_SIMULATION_READY_LOCKED = "SIMULATION_READY_LOCKED"
STATE_SIMULATION_COMPLETE_LOCKED = "SIMULATION_COMPLETE_LOCKED"
STATE_SIMULATION_FAILED_LOCKED = "SIMULATION_FAILED_LOCKED"

REASON_SAFETY_NOT_READY = "EXECUTION_SAFETY_NOT_READY"
REASON_FEEDBACK_NOT_READY = "TRANSPORT_FEEDBACK_NOT_READY"
REASON_FAILURE = "FEEDBACK_FAILURE_DETECTED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledFeedbackLoopInput:
    safety_state: str
    feedback_state: str
    feedback_test_post_confirmed: bool
    feedback_test_output_confirmed: bool
    feedback_zero_post_confirmed: bool
    feedback_zero_output_confirmed: bool
    feedback_failure_detected: bool
    bounded_duration_elapsed: bool = False


@dataclass(frozen=True)
class ControlledFeedbackLoop:
    """Simulation-only feedback adapter for the locked orchestrator.

    It maps already-observed 3B-9 facts back to 3B-7 input fields. It has no
    transport, timer, service call or hardware write primitive.
    """

    state: str
    blockers: tuple[str, ...]
    test_post_confirmed: bool
    test_output_confirmed: bool
    bounded_duration_elapsed: bool
    zero_post_confirmed: bool
    zero_output_confirmed: bool
    failure_detected: bool
    reinjection_allowed: bool
    write_locked: bool
    evaluated_at: str


def evaluate_controlled_feedback_loop(context: ControlledFeedbackLoopInput) -> ControlledFeedbackLoop:
    blockers: list[str] = []
    safety_ready = context.safety_state == "READY_LOCKED"
    if not safety_ready:
        blockers.append(REASON_SAFETY_NOT_READY)

    feedback_known = context.feedback_state in (
        "TEST_CONFIRMED_LOCKED",
        "ZERO_CONFIRMED_LOCKED",
        "FAILED_LOCKED",
    )
    if not feedback_known:
        blockers.append(REASON_FEEDBACK_NOT_READY)

    failure = bool(context.feedback_failure_detected or context.feedback_state == "FAILED_LOCKED")
    if failure:
        blockers.append(REASON_FAILURE)
        state = STATE_SIMULATION_FAILED_LOCKED
    elif context.feedback_zero_post_confirmed and context.feedback_zero_output_confirmed:
        state = STATE_SIMULATION_COMPLETE_LOCKED
    elif safety_ready and feedback_known:
        state = STATE_SIMULATION_READY_LOCKED
    else:
        state = STATE_LOCKED

    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledFeedbackLoop(
        state=state,
        blockers=tuple(blockers),
        test_post_confirmed=bool(context.feedback_test_post_confirmed),
        test_output_confirmed=bool(context.feedback_test_output_confirmed),
        bounded_duration_elapsed=bool(context.bounded_duration_elapsed),
        zero_post_confirmed=bool(context.feedback_zero_post_confirmed),
        zero_output_confirmed=bool(context.feedback_zero_output_confirmed),
        failure_detected=failure,
        reinjection_allowed=False,
        write_locked=True,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
