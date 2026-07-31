from custom_components.carpiquet_ems.digital_twin import TwinBattery, TwinInput, simulate_cycle

def b(soc, max_power=2400):
    return TwinBattery(soc,10,100,5,max_power,max_power,True)

def test_ramp_creates_realistic_import_transient():
    r=simulate_cycle(TwinInput(1500,0,0,0,b(50),b(50),deadband_w=20,ramp_limit_w=100,cycle_seconds=2))
    assert r.hyper_battery_discharge_w <= 100
    assert r.solarflow_battery_discharge_w <= 100
    assert r.grid_w >= 1300

def test_deadband_does_not_chase_small_deficit():
    r=simulate_cycle(TwinInput(15,0,0,0,b(50),b(50),deadband_w=20,ramp_limit_w=500,cycle_seconds=2))
    assert r.mode == 'veille'
    assert r.grid_w == 15

def test_previous_command_ramps_down():
    r=simulate_cycle(TwinInput(0,0,0,0,b(50),b(50),deadband_w=20,ramp_limit_w=100,cycle_seconds=2,previous_hyper_discharge_w=300,previous_solarflow_discharge_w=300))
    assert r.hyper_battery_discharge_w == 200
    assert r.solarflow_battery_discharge_w == 200

def test_all_full_still_blocks_export():
    r=simulate_cycle(TwinInput(500,0,1000,1000,b(100),b(100),deadband_w=20,ramp_limit_w=500,cycle_seconds=2))
    assert not r.grid_export_allowed
    assert r.grid_w == 0
    assert r.curtailed_pv_w == 1500
