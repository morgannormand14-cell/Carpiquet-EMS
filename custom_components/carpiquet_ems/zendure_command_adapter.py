from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

PROFILE_LEGACY_HYPER = "legacy_hyper"
PROFILE_ZENSDK_AC = "zensdk_ac"
PROFILE_UNSUPPORTED = "unsupported"

BINDING_LEGACY_INVOKE = "zendure_legacy.deviceAutomation"
BINDING_ZENSDK_PROPERTIES = "zendure_zensdk.properties_write"


@dataclass(frozen=True)
class HardwareCommandPlan:
    """Read-only, protocol-accurate description of the command Carpiquet would send."""

    control_profile: str
    protocol_generation: str
    operation: str
    service_domain: str
    service: str
    target_entity: str
    payload: dict[str, Any]
    supported: bool
    write_locked: bool = True


@dataclass(frozen=True)
class AdapterCommand:
    device: str
    target_entity: str
    requested_w: float
    prepared_w: float
    observed_w: float
    delta_w: float
    action: str
    reason: str
    would_execute: bool
    hardware_plan: HardwareCommandPlan
    write_locked: bool = True


@dataclass(frozen=True)
class AdapterResult:
    hyper: AdapterCommand
    solarflow: AdapterCommand
    write_locked: bool
    prepared_at: str
    sequence: int


def _legacy_hyper_plan(entity: str, prepared_w: float) -> HardwareCommandPlan:
    """Mirror Zendure-HA Hyper2000.discharge() without executing it."""
    power = max(0, int(round(prepared_w)))
    return HardwareCommandPlan(
        control_profile=PROFILE_LEGACY_HYPER,
        protocol_generation="legacy",
        operation="set_ac_output_power",
        service_domain="zendure_ha",
        service=BINDING_LEGACY_INVOKE,
        target_entity=entity or "Non configurée",
        payload={
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
        },
        supported=True,
    )


def _zensdk_ac_plan(entity: str, prepared_w: float) -> HardwareCommandPlan:
    """Mirror ZendureZenSdk.discharge() without executing it."""
    power = max(0, int(round(prepared_w)))
    return HardwareCommandPlan(
        control_profile=PROFILE_ZENSDK_AC,
        protocol_generation="zensdk",
        operation="set_ac_output_power",
        service_domain="zendure_ha",
        service=BINDING_ZENSDK_PROPERTIES,
        target_entity=entity or "Non configurée",
        payload={
            "properties": {
                "smartMode": 0 if power == 0 else 1,
                "acMode": 2,
                "outputLimit": power,
                "inputLimit": 0,
            },
        },
        supported=True,
    )


def _unsupported_plan(entity: str, prepared_w: float) -> HardwareCommandPlan:
    return HardwareCommandPlan(
        control_profile=PROFILE_UNSUPPORTED,
        protocol_generation="unknown",
        operation="none",
        service_domain="",
        service="",
        target_entity=entity or "Non configurée",
        payload={"requested_w": round(prepared_w, 1)},
        supported=False,
    )


def _prepare_device(
    device: str,
    entity: str,
    requested_w: float,
    observed_w: float,
    previous_w: float | None,
    ramp_limit_w: float,
    deadband_w: float,
    authorized: bool,
    control_profile: str,
) -> AdapterCommand:
    requested = max(0.0, float(requested_w))
    observed = max(0.0, float(observed_w))
    prepared = requested
    reason = "Consigne préparée"

    if previous_w is not None and ramp_limit_w > 0:
        low = max(0.0, previous_w - ramp_limit_w)
        high = previous_w + ramp_limit_w
        limited = max(low, min(high, prepared))
        if abs(limited - prepared) > 0.1:
            prepared = limited
            reason = "Rampe adaptateur appliquée"

    if control_profile == PROFILE_LEGACY_HYPER:
        plan = _legacy_hyper_plan(entity, prepared)
    elif control_profile == PROFILE_ZENSDK_AC:
        plan = _zensdk_ac_plan(entity, prepared)
    else:
        plan = _unsupported_plan(entity, prepared)

    delta = prepared - observed
    if not plan.supported:
        action = "UNSUPPORTED"
        reason = "Profil matériel non supporté"
        would_execute = False
    elif abs(delta) <= max(0.0, deadband_w):
        action = "DEDUPLICATED"
        reason = "Réglage observé déjà conforme"
        would_execute = False
    elif authorized:
        action = "DRY_RUN"
        would_execute = True
    else:
        action = "BLOCKED"
        reason = "Safety State Machine non autorisée"
        would_execute = False

    return AdapterCommand(
        device=device,
        target_entity=entity or "Non configurée",
        requested_w=round(requested, 1),
        prepared_w=round(prepared, 1),
        observed_w=round(observed, 1),
        delta_w=round(delta, 1),
        action=action,
        reason=reason,
        would_execute=would_execute,
        hardware_plan=plan,
        write_locked=True,
    )


def prepare_commands(
    *,
    hyper_entity: str,
    solarflow_entity: str,
    hyper_requested_w: float,
    solarflow_requested_w: float,
    hyper_observed_w: float,
    solarflow_observed_w: float,
    previous_hyper_w: float | None,
    previous_solarflow_w: float | None,
    ramp_limit_w: float = 500.0,
    deadband_w: float = 5.0,
    authorized: bool = False,
    sequence: int = 0,
    hyper_control_profile: str = PROFILE_LEGACY_HYPER,
    solarflow_control_profile: str = PROFILE_ZENSDK_AC,
) -> AdapterResult:
    """Build protocol-accurate, non-executable Zendure command bindings.

    alpha.3.11 deliberately has no execution path. It mirrors the current
    Zendure-HA command shapes for validation while every hardware write remains
    locked.
    """
    hyper = _prepare_device(
        "Hyper 2000", hyper_entity, hyper_requested_w, hyper_observed_w,
        previous_hyper_w, ramp_limit_w, deadband_w, authorized,
        hyper_control_profile,
    )
    solar = _prepare_device(
        "SolarFlow 2400 Pro", solarflow_entity, solarflow_requested_w,
        solarflow_observed_w, previous_solarflow_w, ramp_limit_w, deadband_w,
        authorized, solarflow_control_profile,
    )
    return AdapterResult(
        hyper=hyper,
        solarflow=solar,
        write_locked=True,
        prepared_at=datetime.now(timezone.utc).isoformat(),
        sequence=sequence,
    )
