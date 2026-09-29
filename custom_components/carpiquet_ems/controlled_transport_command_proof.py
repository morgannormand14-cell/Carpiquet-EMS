from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_PROOF_PENDING_LOCKED = "PROOF_PENDING_LOCKED"
STATE_PROOF_READY_LOCKED = "PROOF_READY_LOCKED"

REASON_NO_COMMAND_CONTEXT = "NO_CORRELATABLE_COMMAND_CONTEXT"
REASON_CALL_NOT_REQUESTED = "TRANSPORT_CALL_NOT_REQUESTED"
REASON_CALL_NOT_ALLOWED = "TRANSPORT_CALL_NOT_ALLOWED"
REASON_CALL_NOT_SENT = "TRANSPORT_CALL_NOT_SENT"
REASON_NO_TRANSPORT_RESULT = "NO_TRANSPORT_RESULT"
REASON_NO_POST_PROOF = "NO_INDEPENDENT_POST_PROOF"
REASON_CORRELATION_NOT_CONFIRMED = "CORRELATION_NOT_CONFIRMED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledTransportCommandProofInput:
    command_context_available: bool
    transport_call_requested: bool
    transport_call_allowed: bool
    transport_call_sent: bool
    transport_result_available: bool
    post_proof_available: bool
    correlation_confirmed: bool


@dataclass(frozen=True)
class ControlledTransportCommandProof:
    """Phase 3B-13 strict transport/command proof contract.

    This phase only evaluates evidence produced by the locked 3B chain.
    It contains no transport primitive and cannot authorize or send a command.
    A prepared/requested command is never considered proof of execution.
    """

    state: str
    blockers: tuple[str, ...]
    command_context_available: bool
    transport_call_requested: bool
    transport_call_allowed: bool
    transport_call_sent: bool
    transport_result_available: bool
    post_proof_available: bool
    correlation_confirmed: bool
    proof_chain_complete: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def evaluate_controlled_transport_command_proof(
    context: ControlledTransportCommandProofInput,
) -> ControlledTransportCommandProof:
    blockers: list[str] = []

    if not context.command_context_available:
        blockers.append(REASON_NO_COMMAND_CONTEXT)
    if not context.transport_call_requested:
        blockers.append(REASON_CALL_NOT_REQUESTED)
    if not context.transport_call_allowed:
        blockers.append(REASON_CALL_NOT_ALLOWED)
    if not context.transport_call_sent:
        blockers.append(REASON_CALL_NOT_SENT)
    if not context.transport_result_available:
        blockers.append(REASON_NO_TRANSPORT_RESULT)
    if not context.post_proof_available:
        blockers.append(REASON_NO_POST_PROOF)
    if not context.correlation_confirmed:
        blockers.append(REASON_CORRELATION_NOT_CONFIRMED)

    proof_chain_complete = bool(
        context.command_context_available
        and context.transport_call_requested
        and context.transport_call_allowed
        and context.transport_call_sent
        and context.transport_result_available
        and context.post_proof_available
        and context.correlation_confirmed
    )

    # Even a complete future proof chain remains observational in 3B-13.
    # GLOBAL_WRITE_LOCK is authoritative and reinjection stays impossible.
    blockers.append(REASON_GLOBAL_LOCK)
    state = STATE_PROOF_READY_LOCKED if proof_chain_complete else (
        STATE_PROOF_PENDING_LOCKED
        if context.command_context_available or context.transport_call_requested
        else STATE_LOCKED
    )

    return ControlledTransportCommandProof(
        state=state,
        blockers=tuple(blockers),
        command_context_available=bool(context.command_context_available),
        transport_call_requested=bool(context.transport_call_requested),
        transport_call_allowed=bool(context.transport_call_allowed),
        transport_call_sent=bool(context.transport_call_sent),
        transport_result_available=bool(context.transport_result_available),
        post_proof_available=bool(context.post_proof_available),
        correlation_confirmed=bool(context.correlation_confirmed),
        proof_chain_complete=proof_chain_complete,
        write_locked=True,
        reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
