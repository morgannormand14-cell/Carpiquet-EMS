from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

MODE_SIMULATION = "Simulation"
MODE_SHADOW = "Shadow"
MODE_ARMED = "Armed"

CONTROL_MODES = (MODE_SIMULATION, MODE_SHADOW, MODE_ARMED)

WATCHDOG_OK = "OK"
WATCHDOG_INITIALIZING = "INITIALIZING"
WATCHDOG_GRID_UNAVAILABLE = "GRID_UNAVAILABLE"
WATCHDOG_GRID_STALE = "GRID_STALE"
WATCHDOG_HYPER_UNAVAILABLE = "HYPER_UNAVAILABLE"
WATCHDOG_SOLARFLOW_UNAVAILABLE = "SOLARFLOW_UNAVAILABLE"
WATCHDOG_FALLBACK_BLOCKED = "FALLBACK_BLOCKED"


@dataclass(frozen=True)
class CommandRequest:
    hyper_output_w: float
    solarflow_output_w: float
    hyper_grid_input_w: float = 0.0
    solarflow_grid_input_w: float = 0.0


@dataclass(frozen=True)
class SafetyContext:
    grid_available: bool
    grid_fresh: bool
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
    grid_source_age_seconds: float
    grid_max_age_seconds: float = 60.0


@dataclass(frozen=True)
class CommandDecision:
    requested: CommandRequest
    validated: CommandRequest
    safety_ok: bool
    safety_limited: bool
    safety_reason: str
    watchdog_state: str
    would_send_command: bool
    write_locked: bool
    evaluated_at: str


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _watchdog_reason(context: SafetyContext) -> tuple[str, str] | None:
    if not context.initialization_ready:
        return WATCHDOG_INITIALIZING, "Initialisation moteur incomplète"
    if not context.grid_available:
        return WATCHDOG_GRID_UNAVAILABLE, "Compteur réseau indisponible"
    if not context.grid_fresh:
        return (
            WATCHDOG_GRID_STALE,
            f"Compteur réseau sans actualisation récente ({context.grid_source_age_seconds:.1f} s)",
        )
    if not context.hyper_available:
        return WATCHDOG_HYPER_UNAVAILABLE, "Hyper 2000 indisponible"
    if not context.solarflow_available:
        return WATCHDOG_SOLARFLOW_UNAVAILABLE, "SolarFlow 2400 Pro indisponible"
    if context.fallback_active and not context.allow_fallback:
        return WATCHDOG_FALLBACK_BLOCKED, "Données de secours interdites"
    return None


def evaluate_command(
    mode: str,
    request: CommandRequest,
    context: SafetyContext,
) -> CommandDecision:
    watchdog = _watchdog_reason(context)
    safety_ok = watchdog is None

    hyper_limit = max(0.0, context.hyper_max_power_w)
    solar_limit = max(0.0, context.solarflow_max_power_w)

    # A battery at/below its reserve may not be discharged.
    # Direct PV can still supply the house without consuming the battery.
    if context.hyper_soc <= context.hyper_min_soc:
        hyper_limit = min(hyper_limit, max(0.0, context.hyper_pv_w))
    if context.solarflow_soc <= context.solarflow_min_soc:
        solar_limit = min(solar_limit, max(0.0, context.solarflow_pv_w))

    validated = CommandRequest(
        hyper_output_w=round(_clamp(request.hyper_output_w, 0.0, hyper_limit), 1)
        if safety_ok
        else 0.0,
        solarflow_output_w=round(_clamp(request.solarflow_output_w, 0.0, solar_limit), 1)
        if safety_ok
        else 0.0,
        # Grid charging remains hard-disabled in this Sprint 6 alpha.
        hyper_grid_input_w=0.0,
        solarflow_grid_input_w=0.0,
    )

    limited = (
        abs(validated.hyper_output_w - request.hyper_output_w) > 0.1
        or abs(validated.solarflow_output_w - request.solarflow_output_w) > 0.1
        or abs(validated.hyper_grid_input_w - request.hyper_grid_input_w) > 0.1
        or abs(validated.solarflow_grid_input_w - request.solarflow_grid_input_w) > 0.1
    )

    if watchdog is not None:
        watchdog_state, reason = watchdog
    else:
        watchdog_state = WATCHDOG_OK
        reason = "Consigne limitée par les garde-fous" if limited else "Consigne validée"

    # Shadow means: this command WOULD be sent if Live existed.
    # Real writes remain impossible in v0.6.1.
    return CommandDecision(
        requested=request,
        validated=validated,
        safety_ok=safety_ok,
        safety_limited=limited,
        safety_reason=reason,
        watchdog_state=watchdog_state,
        would_send_command=(mode == MODE_SHADOW and safety_ok),
        write_locked=True,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
