from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ControlledFinalRegressionInput:
    coherence_state: str
    safety_boundary_coherent: bool
    execution_admissible: bool
    coherence_write_locked: bool
    coherence_reinjection_allowed: bool
    identity_state: str
    identity_ready: bool
    independent_transport_proof_verified: bool
    readback_causally_bound: bool
    identity_write_locked: bool
    identity_reinjection_allowed: bool
    recovery_state: str
    recovery_all_passed: bool
    recovery_zero_required: bool
    recovery_zero_confirmed: bool
    recovery_write_locked: bool
    recovery_reinjection_allowed: bool
    recovery_real_transport_used: bool
    loop_success_passed: bool
    loop_failure_passed: bool
    loop_degraded_all_passed: bool
    loop_edge_cases_passed: bool


@dataclass(frozen=True)
class ControlledFinalRegression:
    state: str
    blockers: tuple[str, ...]
    regression_passed: bool
    locked_chain_consistent: bool
    safety_invariants_preserved: bool
    simulation_bench_passed: bool
    evidence_complete: bool
    hardware_test_admissible: bool
    write_locked: bool
    reinjection_allowed: bool
    real_write_used: bool
    evaluated_at: str


def evaluate_controlled_final_regression(context: ControlledFinalRegressionInput) -> ControlledFinalRegression:
    """3B-20 final non-regression verdict. Pure diagnostics; no I/O or authorization."""

    safety = bool(
        context.safety_boundary_coherent
        and not context.execution_admissible
        and context.coherence_write_locked
        and not context.coherence_reinjection_allowed
        and context.identity_write_locked
        and not context.identity_reinjection_allowed
        and context.recovery_write_locked
        and not context.recovery_reinjection_allowed
        and not context.recovery_real_transport_used
    )
    simulation = bool(
        context.recovery_state == "BENCH_PASSED_LOCKED"
        and context.recovery_all_passed
        and context.recovery_zero_required
        and not context.recovery_zero_confirmed
        and context.loop_success_passed
        and context.loop_failure_passed
        and context.loop_degraded_all_passed
        and context.loop_edge_cases_passed
    )
    locked_chain = bool(
        context.coherence_state in ("LOCKED", "COHERENCE_PENDING_LOCKED", "COHERENCE_READY_LOCKED")
        and context.identity_state in ("LOCKED", "IDENTITY_READY_LOCKED", "EVIDENCE_PENDING_LOCKED")
        and safety
    )
    evidence_complete = bool(
        context.identity_ready
        and context.independent_transport_proof_verified
        and context.readback_causally_bound
    )

    blockers: list[str] = []
    if not safety:
        blockers.append("SAFETY_INVARIANT_REGRESSION")
    if not simulation:
        blockers.append("SIMULATION_REGRESSION")
    if not locked_chain:
        blockers.append("LOCKED_CHAIN_INCONSISTENT")
    if not evidence_complete:
        blockers.append("INDEPENDENT_EVIDENCE_INCOMPLETE")
    blockers.append("GLOBAL_WRITE_LOCK")

    regression_passed = bool(safety and simulation and locked_chain)
    # Hard 3B-20 invariant: even a clean regression result cannot authorize hardware.
    hardware_test_admissible = False

    return ControlledFinalRegression(
        state="REGRESSION_PASSED_LOCKED" if regression_passed else "REGRESSION_FAILED_LOCKED",
        blockers=tuple(blockers),
        regression_passed=regression_passed,
        locked_chain_consistent=locked_chain,
        safety_invariants_preserved=safety,
        simulation_bench_passed=simulation,
        evidence_complete=evidence_complete,
        hardware_test_admissible=hardware_test_admissible,
        write_locked=True,
        reinjection_allowed=False,
        real_write_used=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
