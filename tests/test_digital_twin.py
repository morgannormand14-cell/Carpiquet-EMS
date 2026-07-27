from custom_components.carpiquet_ems.digital_twin import TwinBattery,TwinInput,simulate_cycle
def b(soc,max_soc=100,max_power=2400):
    return TwinBattery(soc,10,max_soc,5.0,max_power,max_power,True)
def test_local_surplus_first():
    r=simulate_cycle(TwinInput(600,0,1000,400,b(50),b(50)))
    assert r.hyper_charge_w>0 and r.solarflow_charge_w>0
def test_full_hyper_feeds_solarflow():
    r=simulate_cycle(TwinInput(600,0,1500,300,b(100),b(40)))
    assert r.hyper_charge_w==0 and r.cross_charge_solarflow_w>0
def test_deficit_discharge():
    r=simulate_cycle(TwinInput(1200,0,300,200,b(80),b(80)))
    assert r.hyper_home_w+r.solarflow_home_w>=500
