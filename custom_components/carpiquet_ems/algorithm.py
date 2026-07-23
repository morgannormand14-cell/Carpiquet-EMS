from dataclasses import dataclass

@dataclass(frozen=True)
class BatteryState:
    soc_percent: float
    capacity_kwh: float
    max_power_w: float

@dataclass(frozen=True)
class AllocationResult:
    hyper_power_w: float
    solarflow_power_w: float
    requested_power_w: float
    balance_index_percent: float

def clamp(value, low, high):
    return max(low, min(high, value))

def available_energy_kwh(soc_percent, minimum_soc, capacity_kwh):
    return max(0.0, soc_percent - minimum_soc) / 100.0 * capacity_kwh

def calculate_balance_index(hyper_soc, solarflow_soc):
    return round(clamp(100.0 - abs(hyper_soc - solarflow_soc) * 5.0, 0.0, 100.0), 1)

def allocate_discharge_power(requested_power_w, hyper, solarflow, minimum_soc):
    requested = max(0.0, requested_power_w)
    hyper_energy = available_energy_kwh(hyper.soc_percent, minimum_soc, hyper.capacity_kwh) if hyper.soc_percent > minimum_soc else 0.0
    solar_energy = available_energy_kwh(solarflow.soc_percent, minimum_soc, solarflow.capacity_kwh) if solarflow.soc_percent > minimum_soc else 0.0
    total_energy = hyper_energy + solar_energy
    target = min(requested, hyper.max_power_w + solarflow.max_power_w)

    if target <= 0.0 or total_energy <= 0.0:
        return AllocationResult(0.0, 0.0, round(requested, 1), calculate_balance_index(hyper.soc_percent, solarflow.soc_percent))

    hp = min(target * hyper_energy / total_energy, hyper.max_power_w)
    sp = min(target * solar_energy / total_energy, solarflow.max_power_w)
    remainder = target - hp - sp

    if remainder > 0:
        add = min(remainder, hyper.max_power_w - hp) if hyper_energy > 0 else 0.0
        hp += add
        remainder -= add
    if remainder > 0:
        add = min(remainder, solarflow.max_power_w - sp) if solar_energy > 0 else 0.0
        sp += add

    return AllocationResult(round(hp, 1), round(sp, 1), round(requested, 1), calculate_balance_index(hyper.soc_percent, solarflow.soc_percent))
