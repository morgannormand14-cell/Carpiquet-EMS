from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

STATE_LOCKED = "LOCKED"
STATE_VERIFY_PENDING_LOCKED = "VERIFY_PENDING_LOCKED"
STATE_TEST_CONFIRMED_LOCKED = "TEST_CONFIRMED_LOCKED"
STATE_ZERO_CONFIRMED_LOCKED = "ZERO_CONFIRMED_LOCKED"
STATE_FAILED_LOCKED = "FAILED_LOCKED"
STATE_UNKNOWN_LOCKED = "UNKNOWN_LOCKED"

REASON_BRIDGE_NOT_READY = "TRANSPORT_BRIDGE_NOT_READY"
REASON_NO_RESULT = "NO_TRANSPORT_RESULT"
REASON_HTTP_STATUS = "HTTP_STATUS_NOT_CONFIRMED"
REASON_REPORT_MISSING = "REPORT_NOT_CONFIRMED"
REASON_OUTPUT_MISMATCH = "REPORT_OUTPUT_MISMATCH"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledTransportFeedbackInput:
    bridge_state: str
    bridge_action: str
    expected_output_w: float
    transport_result_available: bool = False
    http_status: int | None = None
    report_available: bool = False
    report_output_w: float | None = None
    failure_detected: bool = False


@dataclass(frozen=True)
class ControlledTransportFeedback:
    """Locked interpretation of future transport/report results.

    Phase 3B-9 is data-only. It never performs HTTP I/O and cannot advance a
    physical device; it only models how observed results will be interpreted.
    """

    state: str
    blockers: tuple[str, ...]
    test_post_confirmed: bool
    test_output_confirmed: bool
    zero_post_confirmed: bool
    zero_output_confirmed: bool
    failure_detected: bool
    report_confirmation_required: bool
    expected_output_w: float
    observed_output_w: float | None
    http_status: int | None
    feedback_ready: bool
    write_locked: bool
    evaluated_at: str


def evaluate_controlled_transport_feedback(
    context: ControlledTransportFeedbackInput,
) -> ControlledTransportFeedback:
    blockers: list[str] = []
    action = context.bridge_action
    test_flow = action in ("POST_TEST_OUTPUT_LIMIT", "VERIFY_REPORT_OUTPUT", "WAIT_BOUNDED_DURATION")
    zero_flow = action in ("POST_ZERO_OUTPUT_LIMIT", "VERIFY_REPORT_ZERO", "RETURN_ZERO_THEN_RELOCK")

    if context.bridge_state != "BRIDGE_READY_LOCKED":
        blockers.append(REASON_BRIDGE_NOT_READY)

    if context.failure_detected:
        state = STATE_FAILED_LOCKED
    elif not context.transport_result_available:
        blockers.append(REASON_NO_RESULT)
        state = STATE_VERIFY_PENDING_LOCKED if (test_flow or zero_flow) else STATE_UNKNOWN_LOCKED
    elif context.http_status is not None and not (200 <= context.http_status < 300):
        blockers.append(REASON_HTTP_STATUS)
        state = STATE_FAILED_LOCKED
    elif not context.report_available:
        blockers.append(REASON_REPORT_MISSING)
        state = STATE_VERIFY_PENDING_LOCKED
    elif context.report_output_w is None:
        blockers.append(REASON_REPORT_MISSING)
        state = STATE_VERIFY_PENDING_LOCKED
    elif abs(float(context.report_output_w) - float(context.expected_output_w)) > 1.0:
        blockers.append(REASON_OUTPUT_MISMATCH)
        state = STATE_FAILED_LOCKED
    elif zero_flow:
        state = STATE_ZERO_CONFIRMED_LOCKED
    elif test_flow:
        state = STATE_TEST_CONFIRMED_LOCKED
    else:
        state = STATE_UNKNOWN_LOCKED

    http_ok = bool(
        context.transport_result_available
        and context.http_status is not None
        and 200 <= context.http_status < 300
    )
    output_ok = bool(
        context.report_available
        and context.report_output_w is not None
        and abs(float(context.report_output_w) - float(context.expected_output_w)) <= 1.0
    )

    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledTransportFeedback(
        state=state,
        blockers=tuple(blockers),
        test_post_confirmed=test_flow and http_ok,
        test_output_confirmed=test_flow and output_ok,
        zero_post_confirmed=zero_flow and http_ok,
        zero_output_confirmed=zero_flow and output_ok,
        failure_detected=context.failure_detected or state == STATE_FAILED_LOCKED,
        report_confirmation_required=True,
        expected_output_w=float(context.expected_output_w),
        observed_output_w=context.report_output_w,
        http_status=context.http_status,
        feedback_ready=state in (STATE_TEST_CONFIRMED_LOCKED, STATE_ZERO_CONFIRMED_LOCKED),
        write_locked=True,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
