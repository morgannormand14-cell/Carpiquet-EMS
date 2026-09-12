from custom_components.carpiquet_ems.generic_energy_engine import GenericSystemInput, allocate_discharge

def s(i,e_soc,cap,power,prev=0,min_soc=10):
    return GenericSystemInput(i,e_soc,min_soc,cap,power,True,prev)

def test_one_system():
    r=allocate_discharge(800,[s('a',50,4,1200)],2,500)
    assert r.allocated_w == 500

def test_two_system_energy_share_and_caps():
    r=allocate_discharge(3600,[s('h',50,3.84,1200,1200),s('s',50,5.28,2400,2400)],2,500)
    assert r.allocated_w == 3600
    assert r.systems[0]['discharge_w'] == 1200
    assert r.systems[1]['discharge_w'] == 2400

def test_five_systems_supported():
    xs=[s(str(i),50,2,1000,1000) for i in range(5)]
    r=allocate_discharge(5000,xs,2,500)
    assert r.allocated_w == 5000
    assert len(r.systems)==5

def test_min_soc_system_gets_zero():
    r=allocate_discharge(1000,[s('a',10,4,1200),s('b',50,4,1200,1000)],2,500)
    assert r.systems[0]['discharge_w']==0
