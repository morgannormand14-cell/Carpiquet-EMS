from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

MODE_SIMULATION = "Simulation"
MODE_SHADOW = "Shadow"
MODE_ARMED = "Armed"

CONTROL_MODES = (MODE_SIMULATION, MODE_SHADOW, MODE_ARMED)


@dataclass(frozen=True)
class CommandRequest:
    hyper_output_w: float
    solarflow_output_w: float
    hyper_grid_input_w: float = 0.0
    solarflow_grid_input_w: float = 0.0


@dataclass(frozen=True)
class SafetyContext:
    grid_available: bool
    hyper_available: bool
    solarflow_available: bool
    initialization_ready: bool
    fallback_active: bool
    allow_fallback: bool
    hyper_soc: float
    solarflow_soc: float
    hyper_min_soc: float
    solarflow_min_soc: float
    hyper_pv_w: float
    solarflow_pv_w: float
    hyper_max_power_w: float
    solarflow_max_power_w: float
    source_age_seconds: float
    max_source_age_seconds: float = 60.0


@dataclass(frozen=True)
class CommandDecision:
    requested: CommandRequest
    validated: CommandRequest
    safety_ok: bool
    safety_limited: bool
    safety_reason: str
    would_send_command: bool
    write_locked: bool
    evaluated_at: str


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def evaluate_command(mode: str, request: CommandRequest, context: SafetyContext) -> CommandDecision:
    reasons: list[str] = []

    if not context.initialization_ready:
        reasons.append("Initialisation moteur incomplète")
    if not context.grid_available:
        reasons.append("Compteur réseau indisponible")
    if not context.hyper_available:
        reasons.append("Hyper 2000 indisponible")
    if not context.solarflow_available:
        reasons.append("SolarFlow 2400 Pro indisponible")
    if context.fallback_active and not context.allow_fallback:
        reasons.append("Données de secours interdites")
    if context.source_age_seconds > context.max_source_age_seconds:
        reasons.append("Données trop anciennes")

    safety_ok = not reasons

    hyper_limit = max(0.0, context.hyper_max_power_w)
    solar_limit = max(0.0, context.solarflow_max_power_w)

    # At/below reserve, the output command is limited to direct PV.
    if context.hyper_soc <= context.hyper_min_soc:
        hyper_limit = min(hyper_limit, max(0.0, context.hyper_pv_w))
    if context.solarflow_soc <= context.solarflow_min_soc:
        solar_limit = min(solar_limit, max(0.0, context.solarflow_pv_w))

    validated = CommandRequest(
        hyper_output_w=round(_clamp(request.hyper_output_w, 0.0, hyper_limit), 1) if safety_ok else 0.0,
        solarflow_output_w=round(_clamp(request.solarflow_output_w, 0.0, solar_limit), 1) if safety_ok else 0.0,
        # AC grid charging remains forbidden in v0.6.0.
        hyper_grid_input_w=0.0,
        solarflow_grid_input_w=0.0,
    )

    limited = (
        abs(validated.hyper_output_w - request.hyper_output_w) > 0.1
        or abs(validated.solarflow_output_w - request.solarflow_output_w) > 0.1
        or abs(validated.hyper_grid_input_w - request.hyper_grid_input_w) > 0.1
        or abs(validated.solarflow_grid_input_w - request.solarflow_grid_input_w) > 0.1
    )

    if safety_ok:
        reasons.append("Consigne limitée par les garde-fous" if limited else "Consigne validée")

    # v0.6.0 never writes. Shadow means "this is what would have been sent".
    return CommandDecision(
        requested=request,
        validated=validated,
        safety_ok=safety_ok,
        safety_limited=limited,
        safety_reason=" ; ".join(reasons) if reasons else "Consigne validée",
        would_send_command=(mode == MODE_SHADOW and safety_ok),
        write_locked=True,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
