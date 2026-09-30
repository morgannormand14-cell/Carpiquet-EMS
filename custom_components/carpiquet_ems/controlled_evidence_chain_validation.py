from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_CHAIN_READY_LOCKED = "CHAIN_READY_LOCKED"
STATE_CHAIN_PENDING_LOCKED = "CHAIN_PENDING_LOCKED"

REASON_TRACE_IDENTITY_NOT_BOUND = "TRACE_IDENTITY_NOT_BOUND"
REASON_EVIDENCE_BINDING_NOT_READY = "EVIDENCE_BINDING_NOT_READY"
REASON_TRANSPORT_PROOF_NOT_BOUND = "TRANSPORT_PROOF_NOT_BOUND"
REASON_READBACK_NOT_BOUND = "READBACK_NOT_BOUND"
REASON_CORRELATION_NOT_BOUND = "CORRELATION_NOT_BOUND"
REASON_EVIDENCE_CHAIN_INCOMPLETE = "EVIDENCE_CHAIN_INCOMPLETE"
REASON_WRITE_LOCK_NOT_PRESERVED = "WRITE_LOCK_NOT_PRESERVED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledEvidenceChainValidationInput:
    trace_identity_bound: bool
    binding_state: str
    transport_proof_bound: bool
    readback_bound: bool
    correlation_bound: bool
    evidence_chain_complete: bool
    upstream_write_locked: bool
    upstream_reinjection_allowed: bool


@dataclass(frozen=True)
class ControlledEvidenceChainValidation:
    """Phase 3B-16 locked end-to-end evidence-chain validation.

    This phase only validates facts produced by 3B-14/3B-15. It has no
    transport primitive, cannot send a request, cannot authorize a write and
    cannot enable feedback reinjection.
    """

    state: str
    blockers: tuple[str, ...]
    trace_identity_valid: bool
    binding_ready: bool
    transport_proof_valid: bool
    readback_valid: bool
    correlation_valid: bool
    evidence_chain_valid: bool
    safety_invariants_preserved: bool
    execution_admissible: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def evaluate_controlled_evidence_chain_validation(
    context: ControlledEvidenceChainValidationInput,
) -> ControlledEvidenceChainValidation:
    blockers: list[str] = []

    trace_identity_valid = bool(context.trace_identity_bound)
    binding_ready = str(context.binding_state or "") == "BINDING_READY_LOCKED"
    transport_proof_valid = bool(context.transport_proof_bound)
    readback_valid = bool(context.readback_bound)
    correlation_valid = bool(context.correlation_bound)
    evidence_chain_valid = bool(
        context.evidence_chain_complete
        and trace_identity_valid
        and binding_ready
        and transport_proof_valid
        and readback_valid
        and correlation_valid
    )
    safety_invariants_preserved = bool(
        context.upstream_write_locked and not context.upstream_reinjection_allowed
    )

    if not trace_identity_valid:
        blockers.append(REASON_TRACE_IDENTITY_NOT_BOUND)
    if not binding_ready:
        blockers.append(REASON_EVIDENCE_BINDING_NOT_READY)
    if not transport_proof_valid:
        blockers.append(REASON_TRANSPORT_PROOF_NOT_BOUND)
    if not readback_valid:
        blockers.append(REASON_READBACK_NOT_BOUND)
    if not correlation_valid:
        blockers.append(REASON_CORRELATION_NOT_BOUND)
    if not evidence_chain_valid:
        blockers.append(REASON_EVIDENCE_CHAIN_INCOMPLETE)
    if not safety_invariants_preserved:
        blockers.append(REASON_WRITE_LOCK_NOT_PRESERVED)

    # 3B-16 is a validation boundary only. Even a complete future evidence
    # chain cannot make execution admissible while GLOBAL_WRITE_LOCK exists.
    execution_admissible = False
    blockers.append(REASON_GLOBAL_LOCK)

    state = (
        STATE_CHAIN_READY_LOCKED
        if trace_identity_valid and binding_ready and safety_invariants_preserved
        else STATE_CHAIN_PENDING_LOCKED
        if trace_identity_valid or binding_ready
        else STATE_LOCKED
    )

    return ControlledEvidenceChainValidation(
        state=state,
        blockers=tuple(blockers),
        trace_identity_valid=trace_identity_valid,
        binding_ready=binding_ready,
        transport_proof_valid=transport_proof_valid,
        readback_valid=readback_valid,
        correlation_valid=correlation_valid,
        evidence_chain_valid=evidence_chain_valid,
        safety_invariants_preserved=safety_invariants_preserved,
        execution_admissible=execution_admissible,
        write_locked=True,
        reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
