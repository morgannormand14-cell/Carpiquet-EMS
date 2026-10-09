from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hmac

STATE_LOCKED = "LOCKED"
STATE_IDENTITY_READY_LOCKED = "IDENTITY_READY_LOCKED"
STATE_EVIDENCE_PENDING_LOCKED = "EVIDENCE_PENDING_LOCKED"
STATE_EVIDENCE_VERIFIED_LOCKED = "EVIDENCE_VERIFIED_LOCKED"

@dataclass(frozen=True)
class ControlledEvidenceIdentityInput:
    trace_identity_bound: bool
    request_id: str
    request_fingerprint: str
    observation_available: bool
    # This independent receipt must be supplied by an actual, audited
    # transport layer. Never derive its identity from the prepared request.
    transport_receipt: dict | None = None

@dataclass(frozen=True)
class ControlledEvidenceIdentity:
    """3B-18 strict identity matching of independently sourced evidence.

    A GET observation, prepared POST envelope or claimed boolean is NOT a
    transport receipt. This module performs no I/O and never grants execution.
    """
    state: str
    blockers: tuple[str, ...]
    identity_ready: bool
    observation_available: bool
    receipt_present: bool
    receipt_identity_matches: bool
    receipt_authenticated: bool
    independent_transport_proof_verified: bool
    readback_causally_bound: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str

def evaluate_controlled_evidence_identity(
    context: ControlledEvidenceIdentityInput,
) -> ControlledEvidenceIdentity:
    rid = str(context.request_id or "")
    fingerprint = str(context.request_fingerprint or "")
    identity_ready = bool(context.trace_identity_bound and rid and len(fingerprint) == 64
                          and all(ch in "0123456789abcdef" for ch in fingerprint))
    receipt = context.transport_receipt if isinstance(context.transport_receipt, dict) else None
    receipt_present = receipt is not None
    receipt_identity_matches = bool(
        identity_ready and receipt_present
        and hmac.compare_digest(str(receipt.get("request_id", "")), rid)
        and hmac.compare_digest(str(receipt.get("request_fingerprint", "")), fingerprint)
    )
    # 3B-18 has no trusted receipt authenticator yet. Matching identifiers
    # alone must NEVER be interpreted as authentic independent POST proof.
    receipt_authenticated = False
    proof_verified = bool(receipt_identity_matches and receipt_authenticated)
    readback_causally_bound = False
    blockers = []
    if not identity_ready:
        blockers.append("TRACE_IDENTITY_NOT_READY")
    if not receipt_present:
        blockers.append("NO_INDEPENDENT_TRANSPORT_RECEIPT")
    elif not receipt_identity_matches:
        blockers.append("TRANSPORT_RECEIPT_IDENTITY_MISMATCH")
    if not receipt_authenticated:
        blockers.append("TRANSPORT_RECEIPT_NOT_AUTHENTICATED")
    if not context.observation_available:
        blockers.append("NO_READBACK_OBSERVATION")
    blockers.append("READBACK_CAUSAL_BINDING_UNPROVEN")
    blockers.append("GLOBAL_WRITE_LOCK")
    state = (
        STATE_EVIDENCE_VERIFIED_LOCKED if proof_verified
        else STATE_EVIDENCE_PENDING_LOCKED if receipt_present and identity_ready
        else STATE_IDENTITY_READY_LOCKED if identity_ready
        else STATE_LOCKED
    )
    return ControlledEvidenceIdentity(
        state=state, blockers=tuple(blockers), identity_ready=identity_ready,
        observation_available=bool(context.observation_available),
        receipt_present=receipt_present, receipt_identity_matches=receipt_identity_matches,
        receipt_authenticated=receipt_authenticated,
        independent_transport_proof_verified=proof_verified,
        readback_causally_bound=readback_causally_bound,
        write_locked=True, reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
