from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

STATE_LOCKED = "LOCKED"
STATE_PREPARED_LOCKED = "PREPARED_LOCKED"

REASON_SEQUENCE_NOT_PREPARED = "CONTROLLED_SEQUENCE_NOT_PREPARED"
REASON_EXECUTOR_NOT_PREPARED = "LOCAL_HTTP_EXECUTOR_NOT_PREPARED"
REASON_INVALID_ENVELOPE = "INVALID_LOCAL_HTTP_ENVELOPE"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class PreparedLocalHttpRequest:
    """A fully inspectable HTTP request description with no I/O primitive."""

    method: str
    target: str
    json_body: dict[str, Any]
    timeout_seconds: float
    prepared: bool
    execution_allowed: bool
    command_sent: bool


@dataclass(frozen=True)
class ControlledLocalHttpPreparation:
    """Phase 3B-5 execution preparation.

    This object deliberately contains data only. It cannot open a socket, issue
    an HTTP request, call a Home Assistant service, or write to SolarFlow.
    """

    state: str
    blockers: tuple[str, ...]
    write_locked: bool
    test_request: PreparedLocalHttpRequest
    zero_request: PreparedLocalHttpRequest
    report_target: str
    verification_required: bool
    return_to_zero_required: bool
    prepared_at: str


def _request(
    *,
    target: str = "",
    body: dict[str, Any] | None = None,
    prepared: bool = False,
) -> PreparedLocalHttpRequest:
    return PreparedLocalHttpRequest(
        method="POST",
        target=target,
        json_body=deepcopy(body or {}),
        timeout_seconds=5.0,
        prepared=prepared,
        execution_allowed=False,
        command_sent=False,
    )


def prepare_controlled_local_http_execution(
    *,
    sequence_state: str,
    executor_prepared: bool,
    target: str,
    report_target: str,
    envelope: dict[str, Any],
) -> ControlledLocalHttpPreparation:
    """Prepare test and mandatory-zero HTTP descriptions without executing them."""

    blockers: list[str] = []
    sequence_ready = sequence_state == "TEST_PREPARED"
    if not sequence_ready:
        blockers.append(REASON_SEQUENCE_NOT_PREPARED)
    if not executor_prepared or not target or not report_target:
        blockers.append(REASON_EXECUTOR_NOT_PREPARED)

    body = deepcopy(envelope) if isinstance(envelope, dict) else {}
    properties = body.get("properties")
    valid = (
        isinstance(properties, dict)
        and bool(body.get("id"))
        and bool(body.get("sn"))
        and "outputLimit" in properties
    )
    if not valid:
        blockers.append(REASON_INVALID_ENVELOPE)

    prepared = not blockers
    zero_body = deepcopy(body)
    if valid:
        zero_body["properties"]["outputLimit"] = 0

    # 3B-5 is preparation only: the global lock remains unconditional.
    blockers.append(REASON_GLOBAL_LOCK)

    return ControlledLocalHttpPreparation(
        state=STATE_PREPARED_LOCKED if prepared else STATE_LOCKED,
        blockers=tuple(blockers),
        write_locked=True,
        test_request=_request(target=target, body=body, prepared=prepared),
        zero_request=_request(target=target, body=zero_body, prepared=prepared),
        report_target=report_target if prepared else "",
        verification_required=True,
        return_to_zero_required=True,
        prepared_at=datetime.now(timezone.utc).isoformat(),
    )
