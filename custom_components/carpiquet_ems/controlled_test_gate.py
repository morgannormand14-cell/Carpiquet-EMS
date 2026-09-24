from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

TEST_GATE_LOCKED = "LOCKED"
TEST_GATE_READY_LOCKED = "READY_LOCKED"
TEST_GATE_ARMED_LOCKED = "ARMED_LOCKED"

REASON_NOT_ARMED = "TEST_NOT_ARMED"
REASON_NO_DEVICE = "NO_SINGLE_TEST_DEVICE"
REASON_POWER = "TEST_POWER_OUT_OF_RANGE"
REASON_DURATION = "TEST_DURATION_OUT_OF_RANGE"
REASON_WATCHDOG = "WATCHDOG_NOT_OK"
REASON_SAFETY = "SAFETY_NOT_OK"
REASON_TRANSPORT = "TRANSPORT_NOT_READY"
REASON_EXECUTOR = "EXECUTOR_NOT_PREPARED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledTestGateInput:
    armed: bool
    device: str
    requested_power_w: float
    duration_seconds: float
    watchdog_ok: bool
    safety_ok: bool
    transport_ready: bool
    executor_prepared: bool


@dataclass(frozen=True)
class ControlledTestGateDecision:
    state: str
    armed: bool
    execute_allowed: bool
    command_sent: bool
    return_to_zero_required: bool
    device: str
    requested_power_w: float
    duration_seconds: float
    blockers: tuple[str, ...]
    evaluated_at: str


def evaluate_controlled_test_gate(context: ControlledTestGateInput) -> ControlledTestGateDecision:
    """Evaluate alpha.3.15 test conditions without permitting any hardware I/O.

    Phase 2 supports an armed-but-locked state and remains non-executable. Even a fully valid test request
    remains behind GLOBAL_WRITE_LOCK until a later, explicitly approved phase.
    """
    blockers: list[str] = []
    if not context.armed:
        blockers.append(REASON_NOT_ARMED)
    if context.device not in ("hyper", "solarflow"):
        blockers.append(REASON_NO_DEVICE)
    if not (1.0 <= context.requested_power_w <= 100.0):
        blockers.append(REASON_POWER)
    if not (1.0 <= context.duration_seconds <= 10.0):
        blockers.append(REASON_DURATION)
    if not context.watchdog_ok:
        blockers.append(REASON_WATCHDOG)
    if not context.safety_ok:
        blockers.append(REASON_SAFETY)
    if not context.transport_ready:
        blockers.append(REASON_TRANSPORT)
    if not context.executor_prepared:
        blockers.append(REASON_EXECUTOR)

    functional_ready = not blockers
    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledTestGateDecision(
        state=(TEST_GATE_READY_LOCKED if functional_ready else (TEST_GATE_ARMED_LOCKED if context.armed else TEST_GATE_LOCKED)),
        armed=context.armed,
        execute_allowed=False,
        command_sent=False,
        return_to_zero_required=True,
        device=context.device,
        requested_power_w=float(context.requested_power_w),
        duration_seconds=float(context.duration_seconds),
        blockers=tuple(blockers),
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
