from __future__ import annotations

from dataclasses import dataclass
from typing import Any

TRANSPORT_MQTT_CANDIDATE = "HA_MQTT_PUBLISH_CANDIDATE"
TRANSPORT_ZENSDK_DUAL_CANDIDATE = "ZENSDK_ATOMIC_DUAL_CANDIDATE"
TRANSPORT_UNRESOLVED = "UNRESOLVED_PUBLIC_SURFACE"
TRANSPORT_UNSUPPORTED = "UNSUPPORTED"

REASON_LEGACY_MQTT = "Legacy function/invoke topic derivable from public HA registry metadata"
REASON_ZENSDK_ATOMIC = "Atomic ZenSDK properties/write is derivable for MQTT and local HTTP; execution remains locked"
REASON_METADATA = "Required Zendure protocol metadata missing"
REASON_UNSUPPORTED = "Hardware control profile unsupported"


@dataclass(frozen=True)
class ExecutionTransport:
    """Non-executable description of a possible public execution transport."""

    profile: str
    kind: str
    public_surface: str
    target: str
    payload: dict[str, Any]
    metadata_ready: bool
    execution_ready: bool
    reason: str
    write_locked: bool = True


def _system_by_profile(inventory: dict[str, Any], profile: str) -> dict[str, Any] | None:
    for system in inventory.get("systems", []):
        if str(system.get("control_profile") or "") == profile:
            return system
    return None


def resolve_execution_transports(
    inventory: dict[str, Any],
    hyper_payload: dict[str, Any],
    solarflow_payload: dict[str, Any],
) -> dict[str, ExecutionTransport]:
    """Resolve candidate public transports without performing any write.

    alpha.3.13 is intentionally transport-observation only. It does not call
    hass.services.async_call(), MQTT publish, HTTP, or Zendure private objects.
    """
    hyper = _system_by_profile(inventory, "legacy_hyper")
    solar = _system_by_profile(inventory, "zensdk_ac")

    if hyper:
        product_key = str(hyper.get("product_key") or "")
        protocol_device_id = str(hyper.get("protocol_device_id") or "")
        if product_key and protocol_device_id:
            hyper_transport = ExecutionTransport(
                profile="legacy_hyper",
                kind=TRANSPORT_MQTT_CANDIDATE,
                public_surface="mqtt.publish",
                target=f"iot/{product_key}/{protocol_device_id}/function/invoke",
                payload=hyper_payload,
                metadata_ready=True,
                execution_ready=False,
                reason=REASON_LEGACY_MQTT,
            )
        else:
            hyper_transport = ExecutionTransport(
                profile="legacy_hyper",
                kind=TRANSPORT_UNRESOLVED,
                public_surface="",
                target="",
                payload=hyper_payload,
                metadata_ready=False,
                execution_ready=False,
                reason=REASON_METADATA,
            )
    else:
        hyper_transport = ExecutionTransport(
            profile="legacy_hyper", kind=TRANSPORT_UNSUPPORTED,
            public_surface="", target="", payload=hyper_payload,
            metadata_ready=False, execution_ready=False, reason=REASON_UNSUPPORTED,
        )

    if solar:
        # ZendureZenSdk.doCommand() sends the same atomic properties payload
        # either to MQTT topic properties/write (cloud transport) or to the
        # device-local HTTP endpoint /properties/write (zenSDK transport).
        # Carpiquet only resolves those candidates here; it executes neither.
        product_key = str(solar.get("product_key") or "")
        protocol_device_id = str(solar.get("protocol_device_id") or "")
        metadata_ready = bool(product_key and protocol_device_id)
        mqtt_target = (
            f"iot/{product_key}/{protocol_device_id}/properties/write"
            if metadata_ready else ""
        )
        solar_transport = ExecutionTransport(
            profile="zensdk_ac",
            kind=TRANSPORT_ZENSDK_DUAL_CANDIDATE if metadata_ready else TRANSPORT_UNRESOLVED,
            public_surface="mqtt.publish | local_http.post",
            target=f"{mqtt_target} | /properties/write" if metadata_ready else "",
            payload=solarflow_payload,
            metadata_ready=metadata_ready,
            execution_ready=False,
            reason=REASON_ZENSDK_ATOMIC if metadata_ready else REASON_METADATA,
        )
    else:
        solar_transport = ExecutionTransport(
            profile="zensdk_ac", kind=TRANSPORT_UNSUPPORTED,
            public_surface="", target="", payload=solarflow_payload,
            metadata_ready=False, execution_ready=False, reason=REASON_UNSUPPORTED,
        )

    return {"hyper": hyper_transport, "solarflow": solar_transport}
