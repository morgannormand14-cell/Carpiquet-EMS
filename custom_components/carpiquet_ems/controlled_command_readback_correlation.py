from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_OBSERVATION_ONLY_LOCKED = "OBSERVATION_ONLY_LOCKED"
STATE_CORRELATION_READY_LOCKED = "CORRELATION_READY_LOCKED"

REASON_NO_POST_PROOF = "NO_TRANSPORT_POST_PROOF"
REASON_NO_COMMAND_CONTEXT = "NO_CORRELATABLE_COMMAND_CONTEXT"
REASON_ACTION_NOT_CORRELATABLE = "ACTION_NOT_CORRELATABLE"
REASON_REPORT_NOT_FORWARDED = "REPORT_NOT_FORWARDED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"

CORRELATABLE_ACTIONS = (
    "POST_TEST_OUTPUT_LIMIT",
    "VERIFY_REPORT_OUTPUT",
    "WAIT_BOUNDED_DURATION",
    "POST_ZERO_OUTPUT_LIMIT",
    "VERIFY_REPORT_ZERO",
    "RETURN_ZERO_THEN_RELOCK",
)


@dataclass(frozen=True)
class ControlledCommandReadbackCorrelationInput:
    bridge_state: str
    bridge_action: str
    expected_output_w: float
    report_forwarded: bool
    observed_output_w: float | None
    post_proof_available: bool


@dataclass(frozen=True)
class ControlledCommandReadbackCorrelation:
    """Phase 3B-12 strict command/readback correlation contract.

    This layer may describe whether a real observation belongs to a
    correlatable command context. It cannot confirm a command unless an
    independent POST proof exists. In the current locked phase that proof is
    always absent, so confirmation and reinjection remain impossible.
    """

    state: str
    blockers: tuple[str, ...]
    command_context_available: bool
    observation_available: bool
    expected_output_w: float
    observed_output_w: float | None
    output_matches_expected: bool
    post_proof_available: bool
    correlation_confirmed: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def evaluate_controlled_command_readback_correlation(
    context: ControlledCommandReadbackCorrelationInput,
) -> ControlledCommandReadbackCorrelation:
    blockers: list[str] = []

    action_correlatable = context.bridge_action in CORRELATABLE_ACTIONS
    command_context = bool(
        context.bridge_state == "BRIDGE_READY_LOCKED" and action_correlatable
    )
    observation_available = bool(
        context.report_forwarded and context.observed_output_w is not None
    )
    output_matches = bool(
        observation_available
        and abs(float(context.observed_output_w) - float(context.expected_output_w)) <= 1.0
    )

    if not command_context:
        blockers.append(REASON_NO_COMMAND_CONTEXT)
        if context.bridge_action and not action_correlatable:
            blockers.append(REASON_ACTION_NOT_CORRELATABLE)
    if not observation_available:
        blockers.append(REASON_REPORT_NOT_FORWARDED)
    if not context.post_proof_available:
        blockers.append(REASON_NO_POST_PROOF)

    # Strict rule: a matching physical observation alone is never proof that
    # our command caused it. Independent POST evidence is mandatory.
    correlation_confirmed = bool(
        command_context
        and observation_available
        and output_matches
        and context.post_proof_available
    )

    if command_context and observation_available:
        state = STATE_CORRELATION_READY_LOCKED
    elif observation_available:
        state = STATE_OBSERVATION_ONLY_LOCKED
    else:
        state = STATE_LOCKED

    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledCommandReadbackCorrelation(
        state=state,
        blockers=tuple(blockers),
        command_context_available=command_context,
        observation_available=observation_available,
        expected_output_w=float(context.expected_output_w),
        observed_output_w=context.observed_output_w if observation_available else None,
        output_matches_expected=output_matches,
        post_proof_available=bool(context.post_proof_available),
        correlation_confirmed=correlation_confirmed,
        write_locked=True,
        reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
