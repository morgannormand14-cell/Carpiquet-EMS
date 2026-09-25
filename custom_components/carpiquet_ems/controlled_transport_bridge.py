from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

STATE_LOCKED = "LOCKED"
STATE_BRIDGE_READY_LOCKED = "BRIDGE_READY_LOCKED"

REASON_ORCHESTRATOR_NOT_READY = "ORCHESTRATOR_NOT_READY"
REASON_PREPARATION_NOT_READY = "LOCAL_HTTP_PREPARATION_NOT_READY"
REASON_SAFETY_NOT_READY = "EXECUTION_SAFETY_NOT_READY"
REASON_TEST_REQUEST_NOT_READY = "TEST_REQUEST_NOT_READY"
REASON_ZERO_REQUEST_NOT_READY = "ZERO_REQUEST_NOT_READY"
REASON_REPORT_TARGET_NOT_READY = "REPORT_TARGET_NOT_READY"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledTransportBridgeInput:
    orchestrator_state: str
    orchestrator_next_action: str
    preparation_state: str
    safety_state: str
    test_request_prepared: bool
    zero_request_prepared: bool
    test_target: str
    test_body: dict[str, Any]
    zero_target: str
    zero_body: dict[str, Any]
    report_target: str


@dataclass(frozen=True)
class ControlledTransportBridge:
    """Locked bridge between the orchestrator and a future HTTP transport.

    It selects inspectable request data only. There is deliberately no HTTP
    client, socket, HA service call, timer or write primitive in this module.
    """

    state: str
    blockers: tuple[str, ...]
    action: str
    method: str
    target: str
    json_body: dict[str, Any]
    report_target: str
    transport_call_requested: bool
    transport_call_allowed: bool
    transport_call_sent: bool
    verification_requested: bool
    zero_return_selected: bool
    write_locked: bool
    evaluated_at: str


def prepare_controlled_transport_bridge(
    context: ControlledTransportBridgeInput,
) -> ControlledTransportBridge:
    blockers: list[str] = []

    if context.preparation_state != "PREPARED_LOCKED":
        blockers.append(REASON_PREPARATION_NOT_READY)
    if context.safety_state != "READY_LOCKED":
        blockers.append(REASON_SAFETY_NOT_READY)
    if not context.test_request_prepared:
        blockers.append(REASON_TEST_REQUEST_NOT_READY)
    if not context.zero_request_prepared:
        blockers.append(REASON_ZERO_REQUEST_NOT_READY)
    if not context.report_target:
        blockers.append(REASON_REPORT_TARGET_NOT_READY)

    action = context.orchestrator_next_action
    write_action = action in ("POST_TEST_OUTPUT_LIMIT", "POST_ZERO_OUTPUT_LIMIT", "RETURN_ZERO_THEN_RELOCK")
    verify_action = action in ("VERIFY_REPORT_OUTPUT", "VERIFY_REPORT_ZERO")

    if context.orchestrator_state in ("LOCKED", "COMPLETE_LOCKED"):
        blockers.append(REASON_ORCHESTRATOR_NOT_READY)

    zero_selected = action in ("POST_ZERO_OUTPUT_LIMIT", "RETURN_ZERO_THEN_RELOCK")
    target = context.zero_target if zero_selected else context.test_target
    body = context.zero_body if zero_selected else context.test_body

    if write_action and (not target or not body):
        blockers.append(REASON_ORCHESTRATOR_NOT_READY)

    functionally_ready = not blockers
    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledTransportBridge(
        state=STATE_BRIDGE_READY_LOCKED if functionally_ready else STATE_LOCKED,
        blockers=tuple(blockers),
        action=action,
        method="GET" if verify_action else "POST" if write_action else "",
        target=context.report_target if verify_action else target if write_action else "",
        json_body={} if verify_action else dict(body) if write_action else {},
        report_target=context.report_target,
        transport_call_requested=write_action or verify_action,
        transport_call_allowed=False,
        transport_call_sent=False,
        verification_requested=verify_action,
        zero_return_selected=zero_selected,
        write_locked=True,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
