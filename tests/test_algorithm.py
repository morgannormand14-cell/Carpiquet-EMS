from custom_components.carpiquet_ems.algorithm import BatteryState, allocate_discharge_power

def hyper(soc):
    return BatteryState(soc, 3.84, 1200)

def solarflow(soc):
    return BatteryState(soc, 5.28, 2400)

def test_import_hyper_at_minimum_solarflow_discharges():
    r = allocate_discharge_power(432.6, hyper(10), solarflow(36), 10)
    assert r.hyper_power_w == 0
    assert r.solarflow_power_w == 432.6

def test_export_no_discharge():
    r = allocate_discharge_power(0, hyper(10), solarflow(36), 10)
    assert r.hyper_power_w == 0
    assert r.solarflow_power_w == 0

def test_below_minimum_is_protected():
    r = allocate_discharge_power(1000, hyper(9), solarflow(50), 10)
    assert r.hyper_power_w == 0
    assert r.solarflow_power_w == 1000

def test_requested_power_is_met():
    r = allocate_discharge_power(1800, hyper(80), solarflow(80), 10)
    assert round(r.hyper_power_w + r.solarflow_power_w, 1) == 1800

def test_limits_are_respected():
    r = allocate_discharge_power(5000, hyper(90), solarflow(90), 10)
    assert r.hyper_power_w <= 1200
    assert r.solarflow_power_w <= 2400
    assert r.hyper_power_w + r.solarflow_power <= 3600

def test_both_at_minimum_are_protected():
    r = allocate_discharge_power(3600, hyper(10), solarflow(10), 10)
    assert r.hyper_power_w == 0
    assert r.solarflow_power_w == 0
