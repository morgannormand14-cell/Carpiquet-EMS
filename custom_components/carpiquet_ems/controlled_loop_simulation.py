from __future__ import annotations

from dataclasses import dataclass

from .controlled_execution_orchestrator import (
    ControlledExecutionOrchestratorInput,
    evaluate_controlled_execution_orchestrator,
)
from .controlled_feedback_loop import (
    ControlledFeedbackLoopInput,
    evaluate_controlled_feedback_loop,
)
from .controlled_transport_feedback import (
    ControlledTransportFeedbackInput,
    evaluate_controlled_transport_feedback,
)

GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class SimulationStep:
    name: str
    orchestrator_state: str
    next_action: str
    feedback_loop_state: str
    write_locked: bool
    execution_allowed: bool
    command_sent: bool


@dataclass(frozen=True)
class ControlledLoopSimulationResult:
    scenario: str
    passed: bool
    steps: tuple[SimulationStep, ...]
    final_state: str
    global_write_lock_preserved: bool
    real_transport_used: bool


def _step(name: str, context: ControlledExecutionOrchestratorInput, feedback_state: str) -> SimulationStep:
    decision = evaluate_controlled_execution_orchestrator(context)
    return SimulationStep(
        name=name,
        orchestrator_state=decision.state,
        next_action=decision.next_action,
        feedback_loop_state=feedback_state,
        write_locked=GLOBAL_LOCK in decision.blockers,
        execution_allowed=decision.execution_allowed,
        command_sent=decision.command_sent,
    )


def simulate_success_path() -> ControlledLoopSimulationResult:
    """Exercise the complete logical loop without transport or timers."""

    steps: list[SimulationStep] = []
    safety = "READY_LOCKED"

    steps.append(_step("test_request", ControlledExecutionOrchestratorInput(safety_state=safety), "LOCKED"))

    # POST acknowledgement first: the orchestrator must explicitly request
    # report verification before accepting the observed output.
    steps.append(_step(
        "test_post_confirmed",
        ControlledExecutionOrchestratorInput(
            safety_state=safety,
            test_post_confirmed=True,
            test_output_confirmed=False,
        ),
        "VERIFY_PENDING_LOCKED",
    ))

    test_loop = evaluate_controlled_feedback_loop(
        ControlledFeedbackLoopInput(
            safety_state=safety,
            feedback_state="TEST_CONFIRMED_LOCKED",
            feedback_test_post_confirmed=True,
            feedback_test_output_confirmed=True,
            feedback_zero_post_confirmed=False,
            feedback_zero_output_confirmed=False,
            feedback_failure_detected=False,
        )
    )
    steps.append(_step(
        "test_confirmed",
        ControlledExecutionOrchestratorInput(
            safety_state=safety,
            test_post_confirmed=test_loop.test_post_confirmed,
            test_output_confirmed=test_loop.test_output_confirmed,
        ),
        test_loop.state,
    ))

    steps.append(_step(
        "duration_elapsed",
        ControlledExecutionOrchestratorInput(
            safety_state=safety,
            test_post_confirmed=True,
            test_output_confirmed=True,
            bounded_duration_elapsed=True,
        ),
        test_loop.state,
    ))

    zero_loop = evaluate_controlled_feedback_loop(
        ControlledFeedbackLoopInput(
            safety_state=safety,
            feedback_state="ZERO_CONFIRMED_LOCKED",
            feedback_test_post_confirmed=True,
            feedback_test_output_confirmed=True,
            feedback_zero_post_confirmed=True,
            feedback_zero_output_confirmed=True,
            feedback_failure_detected=False,
            bounded_duration_elapsed=True,
        )
    )
    # Same rule for the mandatory zero return: POST acknowledgement must
    # transition through VERIFY_REPORT_ZERO before zero output is accepted.
    steps.append(_step(
        "zero_post_confirmed",
        ControlledExecutionOrchestratorInput(
            safety_state=safety,
            test_post_confirmed=True,
            test_output_confirmed=True,
            bounded_duration_elapsed=True,
            zero_post_confirmed=True,
            zero_output_confirmed=False,
        ),
        "VERIFY_PENDING_LOCKED",
    ))

    steps.append(_step(
        "zero_confirmed",
        ControlledExecutionOrchestratorInput(
            safety_state=safety,
            test_post_confirmed=True,
            test_output_confirmed=True,
            bounded_duration_elapsed=True,
            zero_post_confirmed=zero_loop.zero_post_confirmed,
            zero_output_confirmed=zero_loop.zero_output_confirmed,
        ),
        zero_loop.state,
    ))

    expected = (
        ("TEST_READY_LOCKED", "POST_TEST_OUTPUT_LIMIT"),
        ("TEST_VERIFY_LOCKED", "VERIFY_REPORT_OUTPUT"),
        ("TEST_VERIFY_LOCKED", "WAIT_BOUNDED_DURATION"),
        ("ZERO_REQUIRED_LOCKED", "POST_ZERO_OUTPUT_LIMIT"),
        ("ZERO_VERIFY_LOCKED", "VERIFY_REPORT_ZERO"),
        ("COMPLETE_LOCKED", "RELOCK"),
    )
    observed = tuple((s.orchestrator_state, s.next_action) for s in steps)
    lock_ok = all(s.write_locked and not s.execution_allowed and not s.command_sent for s in steps)
    return ControlledLoopSimulationResult(
        scenario="SUCCESS",
        passed=observed == expected and lock_ok,
        steps=tuple(steps),
        final_state=steps[-1].orchestrator_state,
        global_write_lock_preserved=lock_ok,
        real_transport_used=False,
    )


def simulate_failure_path() -> ControlledLoopSimulationResult:
    safety = "READY_LOCKED"
    failure_loop = evaluate_controlled_feedback_loop(
        ControlledFeedbackLoopInput(
            safety_state=safety,
            feedback_state="FAILED_LOCKED",
            feedback_test_post_confirmed=False,
            feedback_test_output_confirmed=False,
            feedback_zero_post_confirmed=False,
            feedback_zero_output_confirmed=False,
            feedback_failure_detected=True,
        )
    )
    step = _step(
        "failure",
        ControlledExecutionOrchestratorInput(
            safety_state=safety,
            failure_detected=failure_loop.failure_detected,
        ),
        failure_loop.state,
    )
    lock_ok = step.write_locked and not step.execution_allowed and not step.command_sent
    passed = (
        step.orchestrator_state == "FAILED_LOCKED"
        and step.next_action == "RETURN_ZERO_THEN_RELOCK"
        and lock_ok
    )
    return ControlledLoopSimulationResult(
        scenario="FAILURE",
        passed=passed,
        steps=(step,),
        final_state=step.orchestrator_state,
        global_write_lock_preserved=lock_ok,
        real_transport_used=False,
    )



def _failure_result(scenario: str, step_name: str, context: ControlledExecutionOrchestratorInput) -> ControlledLoopSimulationResult:
    step = _step(step_name, context, "FAILED_LOCKED")
    lock_ok = step.write_locked and not step.execution_allowed and not step.command_sent
    passed = (
        step.orchestrator_state == "FAILED_LOCKED"
        and step.next_action == "RETURN_ZERO_THEN_RELOCK"
        and lock_ok
    )
    return ControlledLoopSimulationResult(
        scenario=scenario,
        passed=passed,
        steps=(step,),
        final_state=step.orchestrator_state,
        global_write_lock_preserved=lock_ok,
        real_transport_used=False,
    )


def simulate_degraded_paths() -> tuple[ControlledLoopSimulationResult, ...]:
    """Safety-focused degraded scenarios; still pure in-memory simulation."""

    safety = "READY_LOCKED"
    return (
        _failure_result(
            "TEST_POST_FAILED",
            "test_post_failed",
            ControlledExecutionOrchestratorInput(safety_state=safety, failure_detected=True),
        ),
        _failure_result(
            "TEST_REPORT_MISMATCH",
            "test_report_mismatch",
            ControlledExecutionOrchestratorInput(
                safety_state=safety,
                test_post_confirmed=True,
                failure_detected=True,
            ),
        ),
        _failure_result(
            "TEST_TIMEOUT",
            "test_timeout",
            ControlledExecutionOrchestratorInput(
                safety_state=safety,
                test_post_confirmed=True,
                test_output_confirmed=True,
                failure_detected=True,
            ),
        ),
        _failure_result(
            "ZERO_POST_FAILED",
            "zero_post_failed",
            ControlledExecutionOrchestratorInput(
                safety_state=safety,
                test_post_confirmed=True,
                test_output_confirmed=True,
                bounded_duration_elapsed=True,
                failure_detected=True,
            ),
        ),
        _failure_result(
            "ZERO_REPORT_NOT_CONFIRMED",
            "zero_report_not_confirmed",
            ControlledExecutionOrchestratorInput(
                safety_state=safety,
                test_post_confirmed=True,
                test_output_confirmed=True,
                bounded_duration_elapsed=True,
                zero_post_confirmed=True,
                failure_detected=True,
            ),
        ),
    )



def validate_feedback_edge_cases() -> tuple[bool, tuple[str, ...]]:
    """Validate 3B-9 fail-safe semantics used by the degraded scenarios."""

    cases: list[tuple[str, bool]] = []

    missing_status = evaluate_controlled_transport_feedback(
        ControlledTransportFeedbackInput(
            bridge_state="BRIDGE_READY_LOCKED",
            bridge_action="VERIFY_REPORT_OUTPUT",
            expected_output_w=50.0,
            transport_result_available=True,
            http_status=None,
            report_available=True,
            report_output_w=50.0,
        )
    )
    cases.append(("MISSING_HTTP_STATUS_BLOCKED", (
        missing_status.state == "VERIFY_PENDING_LOCKED"
        and not missing_status.feedback_ready
        and not missing_status.test_post_confirmed
    )))

    zero_unconfirmed = evaluate_controlled_transport_feedback(
        ControlledTransportFeedbackInput(
            bridge_state="BRIDGE_READY_LOCKED",
            bridge_action="VERIFY_REPORT_ZERO",
            expected_output_w=0.0,
            transport_result_available=True,
            http_status=200,
            report_available=False,
            report_output_w=None,
        )
    )
    cases.append(("ZERO_REPORT_MISSING_BLOCKED", (
        zero_unconfirmed.state == "VERIFY_PENDING_LOCKED"
        and not zero_unconfirmed.feedback_ready
        and not zero_unconfirmed.zero_output_confirmed
    )))

    zero_mismatch = evaluate_controlled_transport_feedback(
        ControlledTransportFeedbackInput(
            bridge_state="BRIDGE_READY_LOCKED",
            bridge_action="VERIFY_REPORT_ZERO",
            expected_output_w=0.0,
            transport_result_available=True,
            http_status=200,
            report_available=True,
            report_output_w=10.0,
        )
    )
    cases.append(("ZERO_REPORT_MISMATCH_FAILED", (
        zero_mismatch.state == "FAILED_LOCKED"
        and zero_mismatch.failure_detected
        and not zero_mismatch.feedback_ready
    )))

    bridge_locked = evaluate_controlled_transport_feedback(
        ControlledTransportFeedbackInput(
            bridge_state="LOCKED",
            bridge_action="VERIFY_REPORT_OUTPUT",
            expected_output_w=50.0,
            transport_result_available=True,
            http_status=200,
            report_available=True,
            report_output_w=50.0,
        )
    )
    cases.append(("BRIDGE_NOT_READY_LOCKED", (
        bridge_locked.state == "LOCKED"
        and not bridge_locked.feedback_ready
    )))

    return all(ok for _, ok in cases), tuple(
        f"{name}={'PASS' if ok else 'FAIL'}" for name, ok in cases
    )

def run_controlled_loop_simulation() -> tuple[
    ControlledLoopSimulationResult,
    ControlledLoopSimulationResult,
    tuple[ControlledLoopSimulationResult, ...],
    bool,
    tuple[str, ...],
]:
    edge_cases_passed, edge_case_results = validate_feedback_edge_cases()
    return (
        simulate_success_path(),
        simulate_failure_path(),
        simulate_degraded_paths(),
        edge_cases_passed,
        edge_case_results,
    )
