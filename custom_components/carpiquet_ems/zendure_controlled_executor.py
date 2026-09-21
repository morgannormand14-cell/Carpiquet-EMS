from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

EXECUTOR_LOCKED_DRY_RUN = "LOCKED_DRY_RUN"
RESULT_PREPARED_LOCKED = "PREPARED_LOCKED"
RESULT_NOT_PREPARED = "NOT_PREPARED"

TRANSPORT_MQTT = "MQTT"
TRANSPORT_LOCAL_HTTP = "LOCAL_HTTP"


@dataclass(frozen=True)
class PreparedExecution:
    """Final protocol envelope prepared for inspection only.

    alpha.3.14 phase 1 deliberately contains no I/O primitive: no HA service
    call, MQTT publish, HTTP POST, or Zendure private object invocation.
    """

    device: str
    profile: str
    selected_transport: str
    target: str
    envelope: dict[str, Any]
    prepared: bool
    execution_requested: bool
    execution_allowed: bool
    command_sent: bool
    state: str
    reason: str
    prepared_at: str


@dataclass(frozen=True)
class ExecutorResult:
    state: str
    write_locked: bool
    execution_requested: bool
    execution_allowed: bool
    command_sent: bool
    hyper: PreparedExecution
    solarflow: PreparedExecution
    prepared_at: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _system_by_profile(inventory: dict[str, Any], profile: str) -> dict[str, Any] | None:
    for system in inventory.get("systems", []):
        if str(system.get("control_profile") or "") == profile:
            return system
    return None


def _locked(
    *,
    device: str,
    profile: str,
    selected_transport: str,
    target: str = "",
    envelope: dict[str, Any] | None = None,
    prepared: bool = False,
    reason: str,
) -> PreparedExecution:
    return PreparedExecution(
        device=device,
        profile=profile,
        selected_transport=selected_transport,
        target=target,
        envelope=envelope or {},
        prepared=prepared,
        execution_requested=False,
        execution_allowed=False,
        command_sent=False,
        state=RESULT_PREPARED_LOCKED if prepared else RESULT_NOT_PREPARED,
        reason=reason,
        prepared_at=_now(),
    )


def _hyper_execution(
    inventory: dict[str, Any],
    payload: dict[str, Any],
    selected_transport: str,
) -> PreparedExecution:
    system = _system_by_profile(inventory, "legacy_hyper")
    if not system:
        return _locked(
            device="Hyper 2000", profile="legacy_hyper",
            selected_transport=selected_transport,
            reason="Validated Hyper inventory entry unavailable",
        )
    if selected_transport != TRANSPORT_MQTT:
        return _locked(
            device="Hyper 2000", profile="legacy_hyper",
            selected_transport=selected_transport,
            reason="Hyper execution envelope requires selected MQTT transport",
        )

    product_key = str(system.get("product_key") or "")
    device_id = str(system.get("protocol_device_id") or "")
    if not product_key or not device_id:
        return _locked(
            device="Hyper 2000", profile="legacy_hyper",
            selected_transport=selected_transport,
            reason="Hyper MQTT protocol metadata incomplete",
        )

    # ZendureLegacy.mqttInvoke/mqttPublish add runtime messageId/timestamp.
    # Phase 1 uses explicit placeholders rather than inventing live sequence data.
    envelope = deepcopy(payload)
    envelope["messageId"] = "<runtime-message-id>"
    envelope["deviceKey"] = device_id
    envelope["deviceId"] = device_id
    envelope["timestamp"] = "<runtime-unix-timestamp>"
    return _locked(
        device="Hyper 2000",
        profile="legacy_hyper",
        selected_transport=selected_transport,
        target=f"iot/{product_key}/{device_id}/function/invoke",
        envelope=envelope,
        prepared=True,
        reason="Protocol envelope prepared; executor hard-locked, no MQTT publish",
    )


def _solarflow_execution(
    inventory: dict[str, Any],
    payload: dict[str, Any],
    selected_transport: str,
    local_http_qualified: bool,
) -> PreparedExecution:
    system = _system_by_profile(inventory, "zensdk_ac")
    if not system:
        return _locked(
            device="SolarFlow 2400 Pro", profile="zensdk_ac",
            selected_transport=selected_transport,
            reason="Validated SolarFlow inventory entry unavailable",
        )

    product_key = str(system.get("product_key") or "")
    device_id = str(system.get("protocol_device_id") or "")
    serial = str(system.get("serial_number") or system.get("serial") or "")
    host = str(system.get("local_host") or "")

    envelope = deepcopy(payload)
    if selected_transport == TRANSPORT_LOCAL_HTTP:
        if not local_http_qualified:
            return _locked(
                device="SolarFlow 2400 Pro", profile="zensdk_ac",
                selected_transport=selected_transport,
                reason="Selected Local HTTP transport is not qualified",
            )
        if not host or not serial:
            return _locked(
                device="SolarFlow 2400 Pro", profile="zensdk_ac",
                selected_transport=selected_transport,
                reason="SolarFlow Local HTTP metadata incomplete",
            )
        envelope["id"] = "<runtime-http-id>"
        envelope["sn"] = serial
        return _locked(
            device="SolarFlow 2400 Pro",
            profile="zensdk_ac",
            selected_transport=selected_transport,
            target=f"http://{host}/properties/write",
            envelope=envelope,
            prepared=True,
            reason="Protocol envelope prepared; executor hard-locked, no HTTP POST",
        )

    if selected_transport == TRANSPORT_MQTT:
        if not product_key or not device_id:
            return _locked(
                device="SolarFlow 2400 Pro", profile="zensdk_ac",
                selected_transport=selected_transport,
                reason="SolarFlow MQTT protocol metadata incomplete",
            )
        envelope["messageId"] = "<runtime-message-id>"
        envelope["deviceId"] = device_id
        envelope["timestamp"] = "<runtime-unix-timestamp>"
        return _locked(
            device="SolarFlow 2400 Pro",
            profile="zensdk_ac",
            selected_transport=selected_transport,
            target=f"iot/{product_key}/{device_id}/properties/write",
            envelope=envelope,
            prepared=True,
            reason="Protocol envelope prepared; executor hard-locked, no MQTT publish",
        )

    return _locked(
        device="SolarFlow 2400 Pro", profile="zensdk_ac",
        selected_transport=selected_transport,
        reason="SolarFlow selected transport is blocked or unresolved",
    )


def prepare_locked_execution(
    *,
    inventory: dict[str, Any],
    hyper_payload: dict[str, Any],
    solarflow_payload: dict[str, Any],
    hyper_selected_transport: str,
    solarflow_selected_transport: str,
    solarflow_local_http_qualified: bool,
) -> ExecutorResult:
    """Prepare final wire envelopes while making execution impossible by design."""
    hyper = _hyper_execution(inventory, hyper_payload, hyper_selected_transport)
    solar = _solarflow_execution(
        inventory, solarflow_payload, solarflow_selected_transport,
        solarflow_local_http_qualified,
    )
    return ExecutorResult(
        state=EXECUTOR_LOCKED_DRY_RUN,
        write_locked=True,
        execution_requested=False,
        execution_allowed=False,
        command_sent=False,
        hyper=hyper,
        solarflow=solar,
        prepared_at=_now(),
    )
