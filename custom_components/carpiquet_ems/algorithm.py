from dataclasses import dataclass

@dataclass(frozen=True)
class BatteryState:
    soc_percent: float
    capacity_kwh: float
    max_power_w: float
    available: bool = True

@dataclass(frozen=True)
class AllocationResult:
    hyper_power_w: float
    solarflow_power_w: float
    requested_power_w: float
    effective_request_w: float
    unserved_power_w: float
    balance_index_percent: float
    hyper_available_power_w: float
    solarflow_available_power_w: float
    total_available_power_w: float
    active_batteries: int
    limit_reason: str

def clamp(value, low, high):
    return max(low, min(high, value))

def available_energy_kwh(soc_percent, minimum_soc, capacity_kwh):
    return max(0.0, soc_percent-minimum_soc)/100.0*max(0.0,capacity_kwh)

def calculate_balance_index(hyper_soc, solarflow_soc):
    return round(clamp(100.0-abs(hyper_soc-solarflow_soc)*5.0,0.0,100.0),1)

def available_power_w(battery, minimum_soc):
    if not battery.available or battery.soc_percent <= minimum_soc:
        return 0.0
    return max(0.0,battery.max_power_w)

def apply_ramp_limit(requested_power_w, previous_power_w, ramp_limit_w):
    requested=max(0.0,requested_power_w)
    previous=max(0.0,previous_power_w)
    ramp=max(0.0,ramp_limit_w)
    if ramp == 0:
        return requested
    return clamp(requested,max(0.0,previous-ramp),previous+ramp)

def allocate_discharge_power(requested_power_w, hyper, solarflow, minimum_soc,
                             previous_power_w=0.0, ramp_limit_w=0.0):
    requested=max(0.0,requested_power_w)
    effective=apply_ramp_limit(requested,previous_power_w,ramp_limit_w)
    hp_avail=available_power_w(hyper,minimum_soc)
    sp_avail=available_power_w(solarflow,minimum_soc)
    total_avail=hp_avail+sp_avail
    he=available_energy_kwh(hyper.soc_percent,minimum_soc,hyper.capacity_kwh) if hp_avail else 0.0
    se=available_energy_kwh(solarflow.soc_percent,minimum_soc,solarflow.capacity_kwh) if sp_avail else 0.0
    total_energy=he+se
    target=min(effective,total_avail)
    active=int(hp_avail>0)+int(sp_avail>0)

    if requested<=0: reason="no_request"
    elif effective<requested: reason="ramp_limited"
    elif total_avail<=0: reason="no_battery_available"
    elif target<effective: reason="power_limited"
    else: reason="none"

    if target<=0 or total_energy<=0:
        return AllocationResult(0,0,round(requested,1),round(effective,1),round(effective,1),
            calculate_balance_index(hyper.soc_percent,solarflow.soc_percent),
            round(hp_avail,1),round(sp_avail,1),round(total_avail,1),active,reason)

    hp=min(target*he/total_energy,hp_avail)
    sp=min(target*se/total_energy,sp_avail)
    rem=target-hp-sp
    if rem>0 and hp<hp_avail:
        add=min(rem,hp_avail-hp); hp+=add; rem-=add
    if rem>0 and sp<sp_avail:
        sp+=min(rem,sp_avail-sp)
    served=hp+sp
    return AllocationResult(round(hp,1),round(sp,1),round(requested,1),round(effective,1),
        round(max(0.0,effective-served),1),calculate_balance_index(hyper.soc_percent,solarflow.soc_percent),
        round(hp_avail,1),round(sp_avail,1),round(total_avail,1),active,reason)
