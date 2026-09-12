from __future__ import annotations

"""Generic 1..5 system Energy-Aware shadow engine (Sprint 6 / v0.6.5-alpha.3).

This module is intentionally command-free.  It consumes normalized ``systems[]``
style data and calculates an energy-balanced discharge allocation for N systems.
The legacy v0.6.4 twin remains the sole authority while parity is measured.
"""

from dataclasses import dataclass, asdict
from typing import Any

MAX_SYSTEMS = 5


@dataclass(frozen=True)
class GenericSystemInput:
    system_id: str
    soc_percent: float
    min_soc: float
    capacity_kwh: float
    max_discharge_w: float
    available: bool = True
    previous_discharge_w: float = 0.0


@dataclass(frozen=True)
class GenericAllocation:
    requested_w: float
    target_w: float
    allocated_w: float
    unmet_w: float
    systems: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["systems"] = list(self.systems)
        return data


def usable_energy_kwh(system: GenericSystemInput) -> float:
    if not system.available or system.soc_percent <= system.min_soc:
        return 0.0
    return max(0.0, system.capacity_kwh * (system.soc_percent - system.min_soc) / 100.0)


def energy_limited_discharge_w(system: GenericSystemInput, cycle_seconds: float) -> float:
    energy = usable_energy_kwh(system)
    if energy <= 0.0:
        return 0.0
    seconds = max(0.1, float(cycle_seconds))
    energy_limit = energy * 3_600_000.0 / seconds
    return max(0.0, min(float(system.max_discharge_w), energy_limit))


def _ramp(previous: float, target: float, limit_w: float) -> float:
    previous = max(0.0, previous)
    target = max(0.0, target)
    step = max(0.0, limit_w)
    if step <= 0.0:
        return target
    return max(previous - step, min(previous + step, target))


def allocate_discharge(
    demand_w: float,
    systems: list[GenericSystemInput],
    cycle_seconds: float,
    ramp_limit_w: float,
) -> GenericAllocation:
    """Allocate discharge across 1..5 systems by remaining usable energy.

    The initial share is proportional to usable energy above each system's own
    minimum SOC.  Residual demand is water-filled into systems with remaining
    inverter headroom.  Per-system ramping is applied exactly as in the legacy
    v0.6.4 discharge path so two-system parity can be measured in Shadow.
    """
    if not 1 <= len(systems) <= MAX_SYSTEMS:
        raise ValueError(f"Generic engine requires 1..{MAX_SYSTEMS} systems")

    demand = max(0.0, float(demand_w))
    caps = [energy_limited_discharge_w(s, cycle_seconds) for s in systems]
    energies = [usable_energy_kwh(s) if caps[i] > 0.0 else 0.0 for i, s in enumerate(systems)]
    target = min(demand, sum(caps))
    total_energy = sum(energies)

    ideal = [0.0] * len(systems)
    if target > 0.0 and total_energy > 0.0:
        ideal = [min(caps[i], target * energies[i] / total_energy) for i in range(len(systems))]
        remaining = max(0.0, target - sum(ideal))
        # Deterministic water-fill. Repeated passes make the implementation
        # naturally extend to N systems while preserving total available power.
        while remaining > 1e-9:
            progressed = False
            for i in range(len(systems)):
                headroom = max(0.0, caps[i] - ideal[i])
                if headroom <= 0.0:
                    continue
                add = min(remaining, headroom)
                ideal[i] += add
                remaining -= add
                progressed = progressed or add > 0.0
                if remaining <= 1e-9:
                    break
            if not progressed:
                break

    applied = [
        min(caps[i], _ramp(systems[i].previous_discharge_w, ideal[i], ramp_limit_w))
        for i in range(len(systems))
    ]
    rows = tuple({
        "system_id": s.system_id,
        "available": s.available,
        "soc_percent": round(s.soc_percent, 6),
        "min_soc": round(s.min_soc, 6),
        "usable_energy_kwh": round(energies[i], 9),
        "power_cap_w": round(caps[i], 6),
        "ideal_discharge_w": round(ideal[i], 6),
        "discharge_w": round(applied[i], 6),
    } for i, s in enumerate(systems))
    allocated = sum(applied)
    return GenericAllocation(
        requested_w=round(demand, 6),
        target_w=round(target, 6),
        allocated_w=round(allocated, 6),
        unmet_w=round(max(0.0, demand - allocated), 6),
        systems=rows,
    )
