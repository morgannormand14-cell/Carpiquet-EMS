from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

FAILURE_SCENARIOS = (
    "TEST_POST_FAILED",
    "TEST_REPORT_MISMATCH",
    "TEST_TIMEOUT",
    "ZERO_POST_FAILED",
    "ZERO_REPORT_NOT_CONFIRMED",
    "WATCHDOG_LOST",
    "SAFETY_INTERLOCK_LOST",
    "STALE_READBACK",
    "TRANSPORT_RECEIPT_MISMATCH",
)

@dataclass(frozen=True)
class ControlledFailureRecoveryResult:
    scenario: str
    passed: bool
    state: str
    zero_return_required: bool
    zero_return_command_sent: bool
    zero_return_confirmed: bool
    relock_required: bool
    write_locked: bool
    reinjection_allowed: bool
    real_transport_used: bool
    blockers: tuple[str, ...]


def evaluate_locked_failure(scenario: str) -> ControlledFailureRecoveryResult:
    """Fail-closed dry-run obligation, never a real zero-return action.

    An unconfirmed zero return is a critical unresolved condition; the
    simulated request for zero must NEVER be reported as completed.
    """
    known = scenario in FAILURE_SCENARIOS
    blockers = ["GLOBAL_WRITE_LOCK", "ZERO_RETURN_NOT_CONFIRMED"]
    if not known:
        blockers.append("UNKNOWN_FAILURE_SCENARIO")
    return ControlledFailureRecoveryResult(
        scenario=scenario,
        passed=known,
        state="RECOVERY_REQUIRED_LOCKED" if known else "INVALID_SCENARIO_LOCKED",
        zero_return_required=True,
        zero_return_command_sent=False,
        zero_return_confirmed=False,
        relock_required=True,
        write_locked=True,
        reinjection_allowed=False,
        real_transport_used=False,
        blockers=tuple(blockers),
    )


@dataclass(frozen=True)
class ControlledFailureRecoveryBench:
    state: str
    passed_count: int
    total_count: int
    all_passed: bool
    results: tuple[str, ...]
    zero_return_required: bool
    zero_return_confirmed: bool
    write_locked: bool
    reinjection_allowed: bool
    real_transport_used: bool
    evaluated_at: str


def run_locked_failure_recovery_bench() -> ControlledFailureRecoveryBench:
    runs = tuple(evaluate_locked_failure(name) for name in FAILURE_SCENARIOS)
    all_passed = all(
        x.passed
        and x.state == "RECOVERY_REQUIRED_LOCKED"
        and x.zero_return_required
        and not x.zero_return_command_sent
        and not x.zero_return_confirmed
        and x.relock_required
        and x.write_locked
        and not x.reinjection_allowed
        and not x.real_transport_used
        for x in runs
    )
    return ControlledFailureRecoveryBench(
        state="BENCH_PASSED_LOCKED" if all_passed else "BENCH_FAILED_LOCKED",
        passed_count=sum(x.passed for x in runs),
        total_count=len(runs),
        all_passed=all_passed,
        results=tuple(f"{x.scenario}={'PASS' if x.passed else 'FAIL'}" for x in runs),
        zero_return_required=True,
        zero_return_confirmed=False,
        write_locked=True,
        reinjection_allowed=False,
        real_transport_used=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
