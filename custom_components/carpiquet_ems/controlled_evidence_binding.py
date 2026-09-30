from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_LOCKED = "LOCKED"
STATE_BINDING_READY_LOCKED = "BINDING_READY_LOCKED"
STATE_BINDING_PENDING_LOCKED = "BINDING_PENDING_LOCKED"

REASON_TRACE_IDENTITY_NOT_BOUND = "TRACE_IDENTITY_NOT_BOUND"
REASON_NO_REQUEST_ID = "NO_REQUEST_ID"
REASON_NO_REQUEST_FINGERPRINT = "NO_REQUEST_FINGERPRINT"
REASON_NO_TRANSPORT_PROOF = "NO_AUTHENTICATED_TRANSPORT_PROOF"
REASON_NO_READBACK = "NO_READBACK_OBSERVATION"
REASON_CORRELATION_NOT_CONFIRMED = "CORRELATION_NOT_CONFIRMED"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledEvidenceBindingInput:
    trace_identity_bound: bool
    request_id: str
    request_fingerprint: str
    authenticated_transport_proof: bool
    readback_observation_available: bool
    correlation_confirmed: bool


@dataclass(frozen=True)
class ControlledEvidenceBinding:
    """Phase 3B-15 locked evidence-binding contract.

    This binds the immutable 3B-14 request identity to transport/readback
    evidence already produced elsewhere. It has no network primitive, cannot
    manufacture proof, cannot authorize a write and cannot reinject execution.
    """

    state: str
    blockers: tuple[str, ...]
    trace_identity_bound: bool
    request_id: str
    request_fingerprint: str
    transport_proof_bound: bool
    readback_bound: bool
    correlation_bound: bool
    evidence_chain_complete: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def evaluate_controlled_evidence_binding(
    context: ControlledEvidenceBindingInput,
) -> ControlledEvidenceBinding:
    blockers: list[str] = []
    request_id = str(context.request_id or "")
    fingerprint = str(context.request_fingerprint or "")

    if not context.trace_identity_bound:
        blockers.append(REASON_TRACE_IDENTITY_NOT_BOUND)
    if not request_id:
        blockers.append(REASON_NO_REQUEST_ID)
    if not fingerprint:
        blockers.append(REASON_NO_REQUEST_FINGERPRINT)
    if not context.authenticated_transport_proof:
        blockers.append(REASON_NO_TRANSPORT_PROOF)
    if not context.readback_observation_available:
        blockers.append(REASON_NO_READBACK)
    if not context.correlation_confirmed:
        blockers.append(REASON_CORRELATION_NOT_CONFIRMED)

    identity_ready = bool(
        context.trace_identity_bound and request_id and fingerprint
    )
    transport_proof_bound = bool(
        identity_ready and context.authenticated_transport_proof
    )
    readback_bound = bool(
        identity_ready and context.readback_observation_available
    )
    correlation_bound = bool(
        transport_proof_bound
        and readback_bound
        and context.correlation_confirmed
    )
    evidence_chain_complete = bool(
        identity_ready
        and transport_proof_bound
        and readback_bound
        and correlation_bound
    )

    # 3B-15 remains observational. Even a future complete evidence chain
    # cannot unlock writes or feedback reinjection in this phase.
    blockers.append(REASON_GLOBAL_LOCK)
    state = (
        STATE_BINDING_READY_LOCKED
        if identity_ready
        else STATE_BINDING_PENDING_LOCKED
        if (
            context.trace_identity_bound
            or bool(request_id)
            or bool(fingerprint)
            or context.readback_observation_available
        )
        else STATE_LOCKED
    )

    return ControlledEvidenceBinding(
        state=state,
        blockers=tuple(blockers),
        trace_identity_bound=bool(context.trace_identity_bound),
        request_id=request_id,
        request_fingerprint=fingerprint,
        transport_proof_bound=transport_proof_bound,
        readback_bound=readback_bound,
        correlation_bound=correlation_bound,
        evidence_chain_complete=evidence_chain_complete,
        write_locked=True,
        reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
