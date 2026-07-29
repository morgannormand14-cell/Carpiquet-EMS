from __future__ import annotations

from dataclasses import dataclass


FULL_TOLERANCE_PERCENT = 0.05


@dataclass(frozen=True)
class TwinBattery:
    soc_percent: float
    min_soc: float
    max_soc: float
    capacity_kwh: float
    max_discharge_w: float
    max_charge_w: float
    available: bool = True


@dataclass(frozen=True)
class TwinInput:
    house_load_w: float
    grid_target_w: float
    hyper_pv_w: float
    solarflow_pv_w: float
    hyper: TwinBattery
    solarflow: TwinBattery


@dataclass(frozen=True)
class TwinResult:
    mode: str
    hyper_home_w: float
    solarflow_home_w: float
    hyper_pv_to_home_w: float
    solarflow_pv_to_home_w: float
    hyper_battery_discharge_w: float
    solarflow_battery_discharge_w: float
    hyper_charge_w: float
    solarflow_charge_w: float
    hyper_export_pool_w: float
    solarflow_export_pool_w: float
    cross_charge_hyper_w: float
    cross_charge_solarflow_w: float
    grid_w: float
    surplus_w: float
    curtailed_pv_w: float
    grid_export_allowed: bool
    grid_export_block_reason: str
    full_systems_count: int


def _is_full(battery: TwinBattery) -> bool:
    return (
        battery.available
        and battery.soc_percent >= battery.max_soc - FULL_TOLERANCE_PERCENT
    )


def _charge_room_w(battery: TwinBattery) -> float:
    if not battery.available or _is_full(battery):
        return 0.0
    return max(0.0, battery.max_charge_w)


def _discharge_room_w(battery: TwinBattery) -> float:
    if not battery.available or battery.soc_percent <= battery.min_soc:
        return 0.0
    return max(0.0, battery.max_discharge_w)


def _allocate_proportionally(
    demand_w: float,
    hyper_available_w: float,
    solar_available_w: float,
) -> tuple[float, float]:
    demand = max(0.0, demand_w)
    hyper_available = max(0.0, hyper_available_w)
    solar_available = max(0.0, solar_available_w)
    total = hyper_available + solar_available

    if demand <= 0.0 or total <= 0.0:
        return 0.0, 0.0

    hyper = min(hyper_available, demand * hyper_available / total)
    solar = min(solar_available, demand - hyper)

    remaining = max(0.0, demand - hyper - solar)
    if remaining > 0.0:
        extra = min(hyper_available - hyper, remaining)
        hyper += max(0.0, extra)
        remaining -= max(0.0, extra)
    if remaining > 0.0:
        extra = min(solar_available - solar, remaining)
        solar += max(0.0, extra)

    return hyper, solar


def simulate_cycle(data: TwinInput) -> TwinResult:
    house = max(0.0, data.house_load_w)
    hyper_pv = max(0.0, data.hyper_pv_w)
    solar_pv = max(0.0, data.solarflow_pv_w)
    total_pv = hyper_pv + solar_pv

    hyper_full = _is_full(data.hyper)
    solar_full = _is_full(data.solarflow)
    full_systems_count = int(hyper_full) + int(solar_full)
    all_available_systems_full = (
        data.hyper.available
        and data.solarflow.available
        and hyper_full
        and solar_full
    )

    # Pass 1: PV from full systems supplies the house first.
    full_hyper_pv = hyper_pv if hyper_full else 0.0
    full_solar_pv = solar_pv if solar_full else 0.0
    hyper_pv_to_home, solar_pv_to_home = _allocate_proportionally(
        house,
        full_hyper_pv,
        full_solar_pv,
    )

    remaining_house = max(
        0.0,
        house - hyper_pv_to_home - solar_pv_to_home,
    )

    # Pass 2: only if full-system PV is insufficient, use PV from non-full systems.
    non_full_hyper_pv = hyper_pv if not hyper_full else 0.0
    non_full_solar_pv = solar_pv if not solar_full else 0.0
    add_hyper, add_solar = _allocate_proportionally(
        remaining_house,
        non_full_hyper_pv,
        non_full_solar_pv,
    )
    hyper_pv_to_home += add_hyper
    solar_pv_to_home += add_solar
    remaining_house = max(0.0, remaining_house - add_hyper - add_solar)

    # Pass 3: if PV is still insufficient, discharge batteries.
    hyper_battery_discharge, solar_battery_discharge = _allocate_proportionally(
        remaining_house,
        _discharge_room_w(data.hyper),
        _discharge_room_w(data.solarflow),
    )
    remaining_house = max(
        0.0,
        remaining_house
        - hyper_battery_discharge
        - solar_battery_discharge,
    )

    hyper_home = hyper_pv_to_home + hyper_battery_discharge
    solar_home = solar_pv_to_home + solar_battery_discharge

    # Pass 4: local PV surplus charges its own battery first.
    hyper_local_surplus = max(0.0, hyper_pv - hyper_pv_to_home)
    solar_local_surplus = max(0.0, solar_pv - solar_pv_to_home)

    hyper_charge = min(hyper_local_surplus, _charge_room_w(data.hyper))
    solar_charge = min(solar_local_surplus, _charge_room_w(data.solarflow))

    hyper_pool = max(0.0, hyper_local_surplus - hyper_charge)
    solar_pool = max(0.0, solar_local_surplus - solar_charge)

    # Pass 5: one-pass AC redistribution. No energy can loop twice.
    cross_to_solar = min(
        hyper_pool,
        max(0.0, _charge_room_w(data.solarflow) - solar_charge),
    )
    hyper_pool -= cross_to_solar
    solar_charge += cross_to_solar

    cross_to_hyper = min(
        solar_pool,
        max(0.0, _charge_room_w(data.hyper) - hyper_charge),
    )
    solar_pool -= cross_to_hyper
    hyper_charge += cross_to_hyper

    residual_export = max(0.0, hyper_pool + solar_pool)

    # When every system is full, EDF export is prohibited.
    if all_available_systems_full:
        grid_export_allowed = False
        grid_export_block_reason = "Toutes les batteries sont pleines"
        curtailed_pv = residual_export
        exported_to_grid = 0.0
        hyper_pool = 0.0
        solar_pool = 0.0
    else:
        grid_export_allowed = True
        grid_export_block_reason = "Capacité de stockage disponible"
        curtailed_pv = 0.0
        exported_to_grid = residual_export

    # Positive = EDF import. Negative = EDF export.
    grid = remaining_house - exported_to_grid

    if hyper_charge + solar_charge > 0.05:
        mode = "charge"
    elif hyper_battery_discharge + solar_battery_discharge > 0.05:
        mode = "décharge"
    else:
        mode = "veille"

    return TwinResult(
        mode=mode,
        hyper_home_w=round(hyper_home, 1),
        solarflow_home_w=round(solar_home, 1),
        hyper_pv_to_home_w=round(hyper_pv_to_home, 1),
        solarflow_pv_to_home_w=round(solar_pv_to_home, 1),
        hyper_battery_discharge_w=round(hyper_battery_discharge, 1),
        solarflow_battery_discharge_w=round(solar_battery_discharge, 1),
        hyper_charge_w=round(hyper_charge, 1),
        solarflow_charge_w=round(solar_charge, 1),
        hyper_export_pool_w=round(hyper_pool, 1),
        solarflow_export_pool_w=round(solar_pool, 1),
        cross_charge_hyper_w=round(cross_to_hyper, 1),
        cross_charge_solarflow_w=round(cross_to_solar, 1),
        grid_w=round(grid, 1),
        surplus_w=round(max(0.0, total_pv - house), 1),
        curtailed_pv_w=round(curtailed_pv, 1),
        grid_export_allowed=grid_export_allowed,
        grid_export_block_reason=grid_export_block_reason,
        full_systems_count=full_systems_count,
    )
