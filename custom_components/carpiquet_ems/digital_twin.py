from __future__ import annotations
from dataclasses import dataclass

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
    hyper_charge_w: float
    solarflow_charge_w: float
    hyper_export_pool_w: float
    solarflow_export_pool_w: float
    cross_charge_hyper_w: float
    cross_charge_solarflow_w: float
    grid_w: float
    surplus_w: float

def _charge_room_w(b):
    return 0.0 if (not b.available or b.soc_percent >= b.max_soc) else max(0.0, b.max_charge_w)

def _discharge_room_w(b):
    return 0.0 if (not b.available or b.soc_percent <= b.min_soc) else max(0.0, b.max_discharge_w)

def simulate_cycle(data):
    house=max(0.0,data.house_load_w)
    hpv=max(0.0,data.hyper_pv_w)
    spv=max(0.0,data.solarflow_pv_w)
    total_pv=hpv+spv

    if total_pv>0 and house>0:
        hyper_home=min(hpv,house*hpv/total_pv)
        solar_home=min(spv,house*spv/total_pv)
    else:
        hyper_home=solar_home=0.0

    remaining=max(0.0,house-hyper_home-solar_home)
    hroom=_discharge_room_w(data.hyper)
    sroom=_discharge_room_w(data.solarflow)

    total_room=hroom+sroom
    if remaining>0 and total_room>0:
        hdis=min(hroom, remaining*(hroom/total_room))
        sdis=min(sroom, remaining-hdis)
        leftover=remaining-hdis-sdis
        if leftover>0:
            add=min(max(0.0,hroom-hdis),leftover); hdis+=add; leftover-=add
        if leftover>0:
            add=min(max(0.0,sroom-sdis),leftover); sdis+=add
        hyper_home+=hdis
        solar_home+=sdis

    hyper_local=max(0.0,hpv-min(hpv,hyper_home))
    solar_local=max(0.0,spv-min(spv,solar_home))

    hcharge=min(hyper_local,_charge_room_w(data.hyper))
    scharge=min(solar_local,_charge_room_w(data.solarflow))

    hpool=max(0.0,hyper_local-hcharge)
    spool=max(0.0,solar_local-scharge)

    cross_s=min(hpool,max(0.0,_charge_room_w(data.solarflow)-scharge))
    hpool-=cross_s
    scharge+=cross_s

    cross_h=min(spool,max(0.0,_charge_room_w(data.hyper)-hcharge))
    spool-=cross_h
    hcharge+=cross_h

    grid=house-(hyper_home+solar_home)-(hpool+spool)
    if grid>data.grid_target_w: mode="décharge"
    elif grid<data.grid_target_w: mode="charge"
    else: mode="veille"

    return TwinResult(
        mode,
        round(hyper_home,1), round(solar_home,1),
        round(hcharge,1), round(scharge,1),
        round(hpool,1), round(spool,1),
        round(cross_h,1), round(cross_s,1),
        round(grid,1), round(max(0.0,total_pv-house),1),
    )
