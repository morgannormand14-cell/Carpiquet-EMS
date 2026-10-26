"""Hyper 2000 MQTT transition command preparation (NO network I/O).

Reference: Zendure-HA Hyper2000.discharge uses deviceAutomation.
Local/cloud differ in broker connection, not in the deviceAutomation payload.
Never use power_off() as standby: it can place the inverter in OFF.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

TRANSPORTS = frozenset(("LOCAL_MQTT", "CLOUD_MQTT"))


@dataclass(frozen=True)
class PreparedHyperCommand:
    transport: str
    action: str
    allowed: bool
    reason: str
    payload: dict[str, Any] | None
    write_enabled: bool = False


def prepare_hyper_transition(
    action: str,
    *,
    transport: str,
    power_w: int = 0,
    pack_state: str = "unknown",
    soc: float | None = None,
    minimum_soc: float | None = None,
) -> PreparedHyperCommand:
    """Prepare, but never publish, a Zendure-HA-compatible command.

    Caller must confirm a fresh pack state, device transport qualification,
    authorization and feedback before any future physical adapter is enabled.
    """
    if transport not in TRANSPORTS:
        return PreparedHyperCommand(transport, action, False, "unsupported_transport", None)
    if action == "request_standby":
        return PreparedHyperCommand(transport, action, False, "standby_command_unverified_do_not_use_power_off", None)
    if action != "request_discharge":
        return PreparedHyperCommand(transport, action, False, "unsupported_action", None)
    if pack_state != "standby":
        return PreparedHyperCommand(transport, action, False, "pack_not_standby", None)
    try:
        soc_value = float(soc)
        reserve = float(minimum_soc)
        power = int(power_w)
    except (TypeError, ValueError, OverflowError):
        return PreparedHyperCommand(transport, action, False, "invalid_soc_or_power", None)
    if not (0 <= reserve < soc_value <= 100):
        return PreparedHyperCommand(transport, action, False, "soc_reserve", None)
    if not (1 <= power <= 1200) or float(power_w) != power:
        return PreparedHyperCommand(transport, action, False, "power_out_of_range", None)
    payload = {
        "function": "deviceAutomation",
        "arguments": [{
            "autoModelProgram": 2,
            "autoModelValue": {
                "chargingType": 0,
                "chargingPower": 0,
                "freq": 0,
                "outPower": power,
            },
            "msgType": 1,
            "autoModel": 8,
        }],
    }
    # deviceKey, deviceId, messageId, timestamp, MQTT topic and authentication
    # belong to Zendure-HA's authenticated transport, not this pure builder.
    return PreparedHyperCommand(transport, action, True, "prepared_not_authorized", payload)
