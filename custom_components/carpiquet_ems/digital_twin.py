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
    deadband_w: float = 20.0
    ramp_limit_w: float = 500.0
    cycle_seconds: float = 2.0
    previous_hyper_discharge_w: float = 0.0
    previous_solarflow_discharge_w: float = 0.0
    previous_hyper_charge_w: float = 0.0
    previous_solarflow_charge_w: float = 0.0

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


def _is_full(b: TwinBattery) -> bool:
    return b.available and b.soc_percent >= b.max_soc - FULL_TOLERANCE_PERCENT

def _energy_limited_charge_w(b: TwinBattery, cycle_s: float) -> float:
    if not b.available or _is_full(b): return 0.0
    seconds=max(cycle_s,0.1)
    room_kwh=max(0.0,b.capacity_kwh*(b.max_soc-b.soc_percent)/100.0)
    energy_limit=room_kwh*3_600_000.0/seconds
    return max(0.0,min(b.max_charge_w,energy_limit))

def _energy_limited_discharge_w(b: TwinBattery, cycle_s: float) -> float:
    if not b.available or b.soc_percent <= b.min_soc: return 0.0
    seconds=max(cycle_s,0.1)
    usable_kwh=max(0.0,b.capacity_kwh*(b.soc_percent-b.min_soc)/100.0)
    energy_limit=usable_kwh*3_600_000.0/seconds
    return max(0.0,min(b.max_discharge_w,energy_limit))

def _ramp(previous: float, target: float, limit: float) -> float:
    previous=max(0.0,previous); target=max(0.0,target); step=max(0.0,limit)
    if step <= 0: return target
    return max(previous-step,min(previous+step,target))

def _allocate(demand: float, ha: float, sa: float) -> tuple[float,float]:
    demand=max(0.0,demand); ha=max(0.0,ha); sa=max(0.0,sa); total=ha+sa
    if demand<=0 or total<=0: return 0.0,0.0
    h=min(ha,demand*ha/total); s=min(sa,demand-h)
    rem=max(0.0,demand-h-s)
    if rem: x=min(max(0.0,ha-h),rem); h+=x; rem-=x
    if rem: s+=min(max(0.0,sa-s),rem)
    return h,s

def simulate_cycle(d: TwinInput) -> TwinResult:
    house=max(0.0,d.house_load_w); hpv=max(0.0,d.hyper_pv_w); spv=max(0.0,d.solarflow_pv_w)
    hf=_is_full(d.hyper); sf=_is_full(d.solarflow); full_count=int(hf)+int(sf)
    all_full=d.hyper.available and d.solarflow.available and hf and sf

    # Full batteries: their PV is the first solar source for the house.
    hpv_home, spv_home = _allocate(house, hpv if hf else 0.0, spv if sf else 0.0)
    remaining=max(0.0,house-hpv_home-spv_home)
    ah,as_=_allocate(remaining,hpv if not hf else 0.0,spv if not sf else 0.0)
    hpv_home+=ah; spv_home+=as_; remaining=max(0.0,remaining-ah-as_)

    # Deadband: do not chase tiny residual deficits.
    desired_deficit=remaining if remaining>max(0.0,d.deadband_w) else 0.0
    hdes,sdes=_allocate(desired_deficit,_energy_limited_discharge_w(d.hyper,d.cycle_seconds),_energy_limited_discharge_w(d.solarflow,d.cycle_seconds))
    hdis=min(_energy_limited_discharge_w(d.hyper,d.cycle_seconds),_ramp(d.previous_hyper_discharge_w,hdes,d.ramp_limit_w))
    sdis=min(_energy_limited_discharge_w(d.solarflow,d.cycle_seconds),_ramp(d.previous_solarflow_discharge_w,sdes,d.ramp_limit_w))
    remaining=max(0.0,remaining-hdis-sdis)

    hhome=hpv_home+hdis; shome=spv_home+sdis
    hsur=max(0.0,hpv-hpv_home); ssur=max(0.0,spv-spv_home)

    # Deadband: avoid charge adjustments for tiny total surplus.
    total_sur=hsur+ssur
    charge_enabled=total_sur>max(0.0,d.deadband_w)
    hcap=_energy_limited_charge_w(d.hyper,d.cycle_seconds) if charge_enabled else 0.0
    scap=_energy_limited_charge_w(d.solarflow,d.cycle_seconds) if charge_enabled else 0.0
    h_target=min(hsur,hcap); s_target=min(ssur,scap)
    hchg=min(hsur,hcap,_ramp(d.previous_hyper_charge_w,h_target,d.ramp_limit_w))
    schg=min(ssur,scap,_ramp(d.previous_solarflow_charge_w,s_target,d.ramp_limit_w))
    hpool=max(0.0,hsur-hchg); spool=max(0.0,ssur-schg)

    # Cross-charge capacity also respects current ramped charge headroom.
    cross_s=min(hpool,max(0.0,scap-schg)); hpool-=cross_s; schg+=cross_s
    cross_h=min(spool,max(0.0,hcap-hchg)); spool-=cross_h; hchg+=cross_h
    residual=max(0.0,hpool+spool)

    if all_full:
        export_allowed=False; reason='Toutes les batteries sont pleines'; curtailed=residual; exported=0.0; hpool=spool=0.0
    else:
        export_allowed=True; reason='Capacité de stockage disponible'; curtailed=0.0; exported=residual

    grid=remaining-exported
    # Mode is based on flows actually applied, not the ideal target.
    if hchg+schg>0.05: mode='charge'
    elif hdis+sdis>0.05: mode='décharge'
    else: mode='veille'

    return TwinResult(mode,round(hhome,1),round(shome,1),round(hpv_home,1),round(spv_home,1),round(hdis,1),round(sdis,1),round(hchg,1),round(schg,1),round(hpool,1),round(spool,1),round(cross_h,1),round(cross_s,1),round(grid,1),round(max(0.0,hpv+spv-house),1),round(curtailed,1),export_allowed,reason,full_count)
