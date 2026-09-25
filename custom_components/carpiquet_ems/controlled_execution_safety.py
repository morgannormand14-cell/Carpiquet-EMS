from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_READY_LOCKED = "READY_LOCKED"

REASON_PREPARATION_NOT_READY = "LOCAL_HTTP_PREPARATION_NOT_READY"
REASON_WRITE_NOT_LOCKED = "PREPARATION_WRITE_LOCK_MISSING"
REASON_TEST_REQUEST_NOT_READY = "TEST_REQUEST_NOT_READY"
REASON_ZERO_REQUEST_NOT_READY = "ZERO_REQUEST_NOT_READY"
REASON_REPORT_TARGET_NOT_READY = "REPORT_TARGET_NOT_READY"
REASON_INVALID_POWER = "TEST_POWER_OUT_OF_RANGE"
REASON_INVALID_DURATION = "TEST_DURATION_OUT_OF_RANGE"
REASON_WATCHDOG = "WATCHDOG_NOT_OK"
REASON_SAFETY = "SAFETY_NOT_OK"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledExecutionSafetyInput:
    """Inputs for the Phase 3B-6 execution safety contract."""

    preparation_state: str
    preparation_write_locked: bool
    test_request_prepared: bool
    zero_request_prepared: bool
    report_target: str
    requested_power_w: float
    duration_seconds: float
    watchdog_ok: bool
    safety_ok: bool


@dataclass(frozen=True)
class ControlledExecutionSafetyContract:
    """Locked contract for a future single SolarFlow Local HTTP test.

    Phase 3B-6 defines ordering, bounds and fail-safe obligations only.
    It deliberately contains no HTTP client and cannot send a command.
    """

    state: str
    blockers: tuple[str, ...]
    execution_allowed: bool
    command_sent: bool
    single_device_only: bool
    local_http_only: bool
    max_test_power_w: float
    max_duration_seconds: float
    watchdog_required: bool
    verification_required: bool
    zero_return_required: bool
    zero_on_failure_required: bool
    relock_required: bool
    sequence: tuple[str, ...]
    evaluated_at: str


def evaluate_controlled_execution_safety(
    context: ControlledExecutionSafetyInput,
) -> ControlledExecutionSafetyContract:
    """Validate the future execution contract while keeping writes impossible."""

    blockers: list[str] = []

    if context.preparation_state != "PREPARED_LOCKED":
        blockers.append(REASON_PREPARATION_NOT_READY)
    if not context.preparation_write_locked:
        blockers.append(REASON_WRITE_NOT_LOCKED)
    if not context.test_request_prepared:
        blockers.append(REASON_TEST_REQUEST_NOT_READY)
    if not context.zero_request_prepared:
        blockers.append(REASON_ZERO_REQUEST_NOT_READY)
    if not context.report_target:
        blockers.append(REASON_REPORT_TARGET_NOT_READY)
    if not (1.0 <= float(context.requested_power_w) <= 100.0):
        blockers.append(REASON_INVALID_POWER)
    if not (1.0 <= float(context.duration_seconds) <= 10.0):
        blockers.append(REASON_INVALID_DURATION)
    if not context.watchdog_ok:
        blockers.append(REASON_WATCHDOG)
    if not context.safety_ok:
        blockers.append(REASON_SAFETY)

    functionally_ready = not blockers

    # GLOBAL_WRITE_LOCK remains unconditional throughout Phase 3B-6.
    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledExecutionSafetyContract(
        state=STATE_READY_LOCKED if functionally_ready else STATE_LOCKED,
        blockers=tuple(blockers),
        execution_allowed=False,
        command_sent=False,
        single_device_only=True,
        local_http_only=True,
        max_test_power_w=100.0,
        max_duration_seconds=10.0,
        watchdog_required=True,
        verification_required=True,
        zero_return_required=True,
        zero_on_failure_required=True,
        relock_required=True,
        sequence=(
            "AUTHORIZE_SINGLE_TEST",
            "POST_TEST_OUTPUT_LIMIT",
            "VERIFY_POST_STATUS",
            "VERIFY_REPORT_OUTPUT",
            "WAIT_BOUNDED_DURATION",
            "POST_ZERO_OUTPUT_LIMIT",
            "VERIFY_ZERO_POST_STATUS",
            "VERIFY_REPORT_ZERO",
            "RELOCK",
        ),
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
