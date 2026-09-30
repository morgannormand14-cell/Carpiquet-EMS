from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

STATE_LOCKED = "LOCKED"
STATE_TRACE_READY_LOCKED = "TRACE_READY_LOCKED"
STATE_TRACE_PENDING_LOCKED = "TRACE_PENDING_LOCKED"

REASON_NO_COMMAND_CONTEXT = "NO_CORRELATABLE_COMMAND_CONTEXT"
REASON_ACTION_NOT_TRACEABLE = "ACTION_NOT_TRACEABLE"
REASON_REQUEST_NOT_PREPARED = "REQUEST_NOT_PREPARED"
REASON_NO_REQUEST_ID = "NO_REQUEST_ID"
REASON_NO_REQUEST_FINGERPRINT = "NO_REQUEST_FINGERPRINT"
REASON_NO_TRANSPORT_PROOF = "NO_TRANSPORT_PROOF"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"

TRACEABLE_ACTIONS = {
    "POST_TEST_OUTPUT_LIMIT",
    "POST_ZERO_OUTPUT_LIMIT",
    "RETURN_ZERO_THEN_RELOCK",
}


@dataclass(frozen=True)
class ControlledCommandTraceInput:
    command_context_available: bool
    action: str
    method: str
    target: str
    json_body: dict[str, Any]
    request_prepared: bool
    transport_call_sent: bool
    transport_result_available: bool
    post_proof_available: bool


@dataclass(frozen=True)
class ControlledCommandTrace:
    """Phase 3B-14 immutable command identity / trace contract.

    It derives a deterministic identity from an already-prepared request.
    There is no network client, write primitive, HA service call or unlock path.
    Transport proof remains external and mandatory.
    """

    state: str
    blockers: tuple[str, ...]
    command_context_available: bool
    action: str
    request_prepared: bool
    request_id: str
    request_fingerprint: str
    identity_bound: bool
    transport_call_sent: bool
    transport_result_available: bool
    post_proof_available: bool
    authenticated_transport_proof: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def _canonical_request(action: str, method: str, target: str, body: dict[str, Any]) -> str:
    return json.dumps(
        {
            "action": str(action or ""),
            "method": str(method or "").upper(),
            "target": str(target or ""),
            "body": body if isinstance(body, dict) else {},
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def evaluate_controlled_command_trace(
    context: ControlledCommandTraceInput,
) -> ControlledCommandTrace:
    blockers: list[str] = []
    action = str(context.action or "")
    traceable = action in TRACEABLE_ACTIONS

    if not context.command_context_available:
        blockers.append(REASON_NO_COMMAND_CONTEXT)
    if not traceable:
        blockers.append(REASON_ACTION_NOT_TRACEABLE)
    if not context.request_prepared:
        blockers.append(REASON_REQUEST_NOT_PREPARED)

    request_id = ""
    if isinstance(context.json_body, dict):
        request_id = str(context.json_body.get("id") or "")
    if not request_id:
        blockers.append(REASON_NO_REQUEST_ID)

    fingerprint = ""
    if context.request_prepared and traceable and context.target and context.method:
        canonical = _canonical_request(action, context.method, context.target, context.json_body)
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if not fingerprint:
        blockers.append(REASON_NO_REQUEST_FINGERPRINT)

    identity_bound = bool(
        context.command_context_available
        and context.request_prepared
        and traceable
        and request_id
        and fingerprint
    )

    # 3B-14 deliberately cannot manufacture transport evidence. Future
    # authenticated proof must independently bind to this request identity.
    authenticated_transport_proof = bool(
        identity_bound
        and context.transport_call_sent
        and context.transport_result_available
        and context.post_proof_available
    )
    if not authenticated_transport_proof:
        blockers.append(REASON_NO_TRANSPORT_PROOF)

    blockers.append(REASON_GLOBAL_LOCK)
    state = (
        STATE_TRACE_READY_LOCKED
        if identity_bound
        else STATE_TRACE_PENDING_LOCKED
        if context.command_context_available or context.request_prepared
        else STATE_LOCKED
    )

    return ControlledCommandTrace(
        state=state,
        blockers=tuple(blockers),
        command_context_available=bool(context.command_context_available),
        action=action,
        request_prepared=bool(context.request_prepared),
        request_id=request_id,
        request_fingerprint=fingerprint,
        identity_bound=identity_bound,
        transport_call_sent=bool(context.transport_call_sent),
        transport_result_available=bool(context.transport_result_available),
        post_proof_available=bool(context.post_proof_available),
        authenticated_transport_proof=authenticated_transport_proof,
        write_locked=True,
        reinjection_allowed=False,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
