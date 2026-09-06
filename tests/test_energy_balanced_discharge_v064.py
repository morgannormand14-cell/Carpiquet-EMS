from custom_components.carpiquet_ems.digital_twin import TwinBattery, _allocate_discharge_energy_balanced

def b(soc, cap, pmax, min_soc=10):
    return TwinBattery(soc, min_soc, 100, cap, pmax, pmax, True)

def test_equal_soc_uses_capacity_ratio():
    h,s = _allocate_discharge_energy_balanced(1000, b(80,3.84,1200), b(80,5.28,2400), 2)
    assert round(h+s, 6) == 1000
    assert 415 < h < 430
    assert 570 < s < 585

def test_lower_solar_soc_shifts_load_to_hyper():
    h,s = _allocate_discharge_energy_balanced(600, b(30.6,3.84,1200), b(10.3,5.28,2400), 2)
    assert h > 580
    assert s < 20

def test_full_combined_power_is_preserved():
    h,s = _allocate_discharge_energy_balanced(3600, b(80,3.84,1200), b(80,5.28,2400), 2)
    assert h == 1200
    assert s == 2400

def test_min_soc_removes_only_depleted_system():
    h,s = _allocate_discharge_energy_balanced(1000, b(10,3.84,1200), b(50,5.28,2400), 2)
    assert h == 0
    assert s == 1000
