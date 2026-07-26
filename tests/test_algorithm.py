from custom_components.carpiquet_ems.algorithm import BatteryState,allocate_discharge_power,apply_ramp_limit

def test_ramp_limit():
    assert apply_ramp_limit(2000,500,300)==800

def test_unavailable_battery():
    r=allocate_discharge_power(1000,BatteryState(90,3.84,1200,False),
        BatteryState(90,5.28,2400,True),10)
    assert r.hyper_power_w==0 and r.solarflow_power_w==1000 and r.active_batteries==1

def test_soc_reserve():
    r=allocate_discharge_power(1000,BatteryState(10,3.84,1200),
        BatteryState(10,5.28,2400),10)
    assert r.total_available_power_w==0
    assert r.limit_reason=="no_battery_available"

def test_power_limit():
    r=allocate_discharge_power(5000,BatteryState(90,3.84,1200),
        BatteryState(90,5.28,2400),10)
    assert r.total_available_power_w==3600
    assert r.hyper_power_w<=1200 and r.solarflow_power_w<=2400
