from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ControlledHardwarePreflightInput:
    final_regression_passed: bool
    locked_chain_consistent: bool
    safety_invariants_preserved: bool
    simulation_bench_passed: bool
    independent_evidence_complete: bool
    final_write_locked: bool
    final_reinjection_allowed: bool
    real_write_used: bool
    test_power_w: float
    power_limit_w: float
    duration_seconds: float
    single_device_only: bool
    local_http_only: bool
    watchdog_required: bool
    verification_required: bool
    zero_return_required: bool
    zero_on_failure_required: bool
    relock_required: bool
    test_request_prepared: bool
    zero_request_prepared: bool
    report_target_ready: bool
    test_armed: bool
    solarflow_selected: bool
    local_http_qualified: bool
    explicit_write_authorized: bool


@dataclass(frozen=True)
class ControlledHardwarePreflight:
    state: str
    blockers: tuple[str, ...]
    audit_passed: bool
    regression_ready: bool
    bounds_ready: bool
    recovery_contract_ready: bool
    independent_evidence_ready: bool
    protocol_ready: bool
    unlock_eligible: bool
    hardware_test_admissible: bool
    explicit_human_authorization_required: bool
    write_locked: bool
    reinjection_allowed: bool
    real_write_used: bool
    evaluated_at: str


def evaluate_controlled_hardware_preflight(context: ControlledHardwarePreflightInput) -> ControlledHardwarePreflight:
    """3B-21 final preflight audit. Diagnostic only; cannot unlock hardware."""

    regression_ready = bool(
        context.final_regression_passed
        and context.locked_chain_consistent
        and context.safety_invariants_preserved
        and context.simulation_bench_passed
        and context.final_write_locked
        and not context.final_reinjection_allowed
        and not context.real_write_used
    )
    bounds_ready = bool(
        0.0 < float(context.test_power_w) <= 2400.0
        and 0.0 <= float(context.power_limit_w) <= 2400.0
        and float(context.test_power_w) <= float(context.power_limit_w)
        and 1.0 <= float(context.duration_seconds) <= 10.0
        and context.single_device_only
        and context.local_http_only
    )
    recovery_ready = bool(
        context.watchdog_required
        and context.verification_required
        and context.zero_return_required
        and context.zero_on_failure_required
        and context.relock_required
        and context.test_request_prepared
        and context.zero_request_prepared
        and context.report_target_ready
    )
    evidence_ready = bool(context.independent_evidence_complete)
    protocol_ready = bool(regression_ready and bounds_ready and recovery_ready)

    blockers: list[str] = []
    if not regression_ready:
        blockers.append("FINAL_REGRESSION_NOT_READY")
    if not bounds_ready:
        blockers.append("CONTROLLED_TEST_BOUNDS_NOT_READY")
    if not recovery_ready:
        blockers.append("ZERO_RETURN_PROTOCOL_NOT_READY")
    # Independent POST evidence is necessarily produced after the first POST;
    # it is a required result of the test, not a circular prerequisite to it.
    unlock_eligible = bool(protocol_ready and context.test_armed and context.solarflow_selected
                           and context.local_http_qualified)
    if not context.test_armed:
        blockers.append("CONTROLLED_TEST_NOT_ARMED")
    if not context.solarflow_selected:
        blockers.append("SOLARFLOW_NOT_SELECTED")
    if not context.local_http_qualified:
        blockers.append("LOCAL_HTTP_NOT_QUALIFIED")
    if not context.explicit_write_authorized:
        blockers.append("EXPLICIT_HUMAN_AUTHORIZATION_REQUIRED")
    hardware_test_admissible = bool(unlock_eligible and context.explicit_write_authorized)
    if not hardware_test_admissible:
        blockers.append("GLOBAL_WRITE_LOCK")
    audit_passed = bool(protocol_ready)

    return ControlledHardwarePreflight(
        state="PREFLIGHT_READY_LOCKED" if audit_passed else "PREFLIGHT_BLOCKED_LOCKED",
        blockers=tuple(blockers),
        audit_passed=audit_passed,
        regression_ready=regression_ready,
        bounds_ready=bounds_ready,
        recovery_contract_ready=recovery_ready,
        independent_evidence_ready=evidence_ready,
        protocol_ready=protocol_ready,
        unlock_eligible=unlock_eligible,
        hardware_test_admissible=hardware_test_admissible,
        explicit_human_authorization_required=True,
        write_locked=True,
        reinjection_allowed=False,
        real_write_used=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
