from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_COHERENCE_PENDING_LOCKED = "COHERENCE_PENDING_LOCKED"
STATE_COHERENCE_READY_LOCKED = "COHERENCE_READY_LOCKED"

REASON_TRACE_IDENTITY_NOT_VALID = "TRACE_IDENTITY_NOT_VALID"
REASON_BINDING_NOT_READY = "BINDING_NOT_READY"
REASON_READBACK_NOT_VALID = "READBACK_NOT_VALID"
REASON_TRANSPORT_PROOF_NOT_VALID = "TRANSPORT_PROOF_NOT_VALID"
REASON_CORRELATION_NOT_VALID = "CORRELATION_NOT_VALID"
REASON_EVIDENCE_CHAIN_NOT_VALID = "EVIDENCE_CHAIN_NOT_VALID"
REASON_SAFETY_INVARIANTS_NOT_PRESERVED = "SAFETY_INVARIANTS_NOT_PRESERVED"
REASON_UPSTREAM_EXECUTION_ADMISSIBLE = "UPSTREAM_EXECUTION_ADMISSIBLE"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledPreExecutionCoherenceInput:
    trace_identity_valid: bool
    binding_ready: bool
    transport_proof_valid: bool
    readback_valid: bool
    correlation_valid: bool
    evidence_chain_valid: bool
    safety_invariants_preserved: bool
    upstream_execution_admissible: bool
    upstream_write_locked: bool
    upstream_reinjection_allowed: bool


@dataclass(frozen=True)
class ControlledPreExecutionCoherence:
    """Phase 3B-17 locked pre-execution coherence boundary.

    This module does not execute, authorize, or transport commands. It checks
    that the 3B-16 evidence result is internally coherent while preserving the
    global lock. A future complete proof chain can be reported as coherent,
    but execution remains forbidden in this phase.
    """

    state: str
    blockers: tuple[str, ...]
    identity_coherent: bool
    binding_coherent: bool
    readback_coherent: bool
    transport_proof_coherent: bool
    correlation_coherent: bool
    evidence_chain_coherent: bool
    safety_boundary_coherent: bool
    pre_execution_coherent: bool
    execution_admissible: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def evaluate_controlled_pre_execution_coherence(
    context: ControlledPreExecutionCoherenceInput,
) -> ControlledPreExecutionCoherence:
    blockers: list[str] = []

    identity_coherent = bool(context.trace_identity_valid)
    binding_coherent = bool(context.binding_ready and identity_coherent)
    readback_coherent = bool(context.readback_valid and binding_coherent)
    transport_proof_coherent = bool(context.transport_proof_valid and binding_coherent)
    correlation_coherent = bool(
        context.correlation_valid
        and transport_proof_coherent
        and readback_coherent
    )
    evidence_chain_coherent = bool(
        context.evidence_chain_valid
        and identity_coherent
        and binding_coherent
        and transport_proof_coherent
        and readback_coherent
        and correlation_coherent
    )
    safety_boundary_coherent = bool(
        context.safety_invariants_preserved
        and context.upstream_write_locked
        and not context.upstream_reinjection_allowed
        and not context.upstream_execution_admissible
    )

    if not identity_coherent:
        blockers.append(REASON_TRACE_IDENTITY_NOT_VALID)
    if not binding_coherent:
        blockers.append(REASON_BINDING_NOT_READY)
    if not readback_coherent:
        blockers.append(REASON_READBACK_NOT_VALID)
    if not transport_proof_coherent:
        blockers.append(REASON_TRANSPORT_PROOF_NOT_VALID)
    if not correlation_coherent:
        blockers.append(REASON_CORRELATION_NOT_VALID)
    if not evidence_chain_coherent:
        blockers.append(REASON_EVIDENCE_CHAIN_NOT_VALID)
    if not safety_boundary_coherent:
        blockers.append(REASON_SAFETY_INVARIANTS_NOT_PRESERVED)
    if context.upstream_execution_admissible:
        blockers.append(REASON_UPSTREAM_EXECUTION_ADMISSIBLE)

    pre_execution_coherent = bool(
        evidence_chain_coherent and safety_boundary_coherent
    )

    # Hard invariant for 3B-17: this is diagnostic preparation only.
    execution_admissible = False
    blockers.append(REASON_GLOBAL_LOCK)

    state = (
        STATE_COHERENCE_READY_LOCKED
        if identity_coherent and binding_coherent and safety_boundary_coherent
        else STATE_COHERENCE_PENDING_LOCKED
        if identity_coherent or binding_coherent or readback_coherent
        else STATE_LOCKED
    )

    return ControlledPreExecutionCoherence(
        state=state,
        blockers=tuple(blockers),
        identity_coherent=identity_coherent,
        binding_coherent=binding_coherent,
        readback_coherent=readback_coherent,
        transport_proof_coherent=transport_proof_coherent,
        correlation_coherent=correlation_coherent,
        evidence_chain_coherent=evidence_chain_coherent,
        safety_boundary_coherent=safety_boundary_coherent,
        pre_execution_coherent=pre_execution_coherent,
        execution_admissible=execution_admissible,
        write_locked=True,
        reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
