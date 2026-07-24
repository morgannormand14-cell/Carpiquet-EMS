from custom_components.carpiquet_ems.algorithm import BatteryState, allocate_discharge_power, calculate_balance_index

def test_zero_request():
    result = allocate_discharge_power(0, BatteryState(50, 3.84, 1200), BatteryState(50, 5.28, 2400), 10)
    assert result.hyper_power_w == 0
    assert result.solarflow_power_w == 0

def test_soc_protection():
    result = allocate_discharge_power(1000, BatteryState(10, 3.84, 1200), BatteryState(10, 5.28, 2400), 10)
    assert result.hyper_power_w == 0
    assert result.solarflow_power_w == 0

def test_balance_index():
    assert calculate_balance_index(50, 50) == 100
    assert calculate_balance_index(50, 60) == 50

def test_power_limits():
    result = allocate_discharge_power(5000, BatteryState(90, 3.84, 1200), BatteryState(90, 5.28, 2400), 10)
    assert result.hyper_power_w <= 1200
    assert result.solarflow_power_w <= 2400
