from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


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
    write_locked: bool = True


@dataclass(frozen=True)
class AdapterResult:
    hyper: AdapterCommand
    solarflow: AdapterCommand
    write_locked: bool
    prepared_at: str
    sequence: int


def _prepare_device(device: str, entity: str, requested_w: float, observed_w: float,
                    previous_w: float | None, ramp_limit_w: float, deadband_w: float,
                    authorized: bool) -> AdapterCommand:
    requested = max(0.0, float(requested_w))
    observed = max(0.0, float(observed_w))
    prepared = requested
    reason = "Consigne préparée"

    # Adapter-side ramp limiter: an additional defence after the Safety Controller.
    if previous_w is not None and ramp_limit_w > 0:
        low = max(0.0, previous_w - ramp_limit_w)
        high = previous_w + ramp_limit_w
        limited = max(low, min(high, prepared))
        if abs(limited - prepared) > 0.1:
            prepared = limited
            reason = "Rampe adaptateur appliquée"

    delta = prepared - observed
    if abs(delta) <= max(0.0, deadband_w):
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
        write_locked=True,
    )


def prepare_commands(*, hyper_entity: str, solarflow_entity: str,
                     hyper_requested_w: float, solarflow_requested_w: float,
                     hyper_observed_w: float, solarflow_observed_w: float,
                     previous_hyper_w: float | None, previous_solarflow_w: float | None,
                     ramp_limit_w: float = 500.0, deadband_w: float = 5.0,
                     authorized: bool = False, sequence: int = 0) -> AdapterResult:
    """Translate validated EMS outputs into dry-run Zendure commands.

    v0.6.4-alpha is deliberately non-executable: this module never calls Home
    Assistant services and every result carries write_locked=True.
    """
    hyper = _prepare_device("Hyper 2000", hyper_entity, hyper_requested_w,
                            hyper_observed_w, previous_hyper_w, ramp_limit_w,
                            deadband_w, authorized)
    solar = _prepare_device("SolarFlow 2400 Pro", solarflow_entity,
                            solarflow_requested_w, solarflow_observed_w,
                            previous_solarflow_w, ramp_limit_w, deadband_w,
                            authorized)
    return AdapterResult(
        hyper=hyper,
        solarflow=solar,
        write_locked=True,
        prepared_at=datetime.now(timezone.utc).isoformat(),
        sequence=sequence,
    )
