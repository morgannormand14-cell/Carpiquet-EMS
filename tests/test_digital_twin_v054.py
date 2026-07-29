from custom_components.carpiquet_ems.digital_twin import (
    TwinBattery,
    TwinInput,
    simulate_cycle,
)


def battery(soc, max_soc=100.0, max_power=2400.0):
    return TwinBattery(
        soc_percent=soc,
        min_soc=10.0,
        max_soc=max_soc,
        capacity_kwh=5.0,
        max_discharge_w=max_power,
        max_charge_w=max_power,
        available=True,
    )


def test_full_system_pv_supplies_house_before_non_full_system():
    result = simulate_cycle(
        TwinInput(
            house_load_w=600,
            grid_target_w=0,
            hyper_pv_w=700,
            solarflow_pv_w=500,
            hyper=battery(100),
            solarflow=battery(70),
        )
    )
    assert result.hyper_pv_to_home_w == 600
    assert result.solarflow_pv_to_home_w == 0
    assert result.solarflow_charge_w >= 500


def test_non_full_system_pv_used_only_when_full_system_is_insufficient():
    result = simulate_cycle(
        TwinInput(
            house_load_w=900,
            grid_target_w=0,
            hyper_pv_w=700,
            solarflow_pv_w=500,
            hyper=battery(100),
            solarflow=battery(70),
        )
    )
    assert result.hyper_pv_to_home_w == 700
    assert result.solarflow_pv_to_home_w == 200
    assert result.solarflow_charge_w >= 300


def test_all_full_blocks_edf_export_and_curtaills_surplus():
    result = simulate_cycle(
        TwinInput(
            house_load_w=600,
            grid_target_w=0,
            hyper_pv_w=1000,
            solarflow_pv_w=800,
            hyper=battery(100),
            solarflow=battery(100),
        )
    )
    assert result.grid_export_allowed is False
    assert result.grid_w == 0
    assert result.curtailed_pv_w == 1200


def test_export_is_reenabled_when_one_system_is_below_max_soc():
    result = simulate_cycle(
        TwinInput(
            house_load_w=600,
            grid_target_w=0,
            hyper_pv_w=1000,
            solarflow_pv_w=3000,
            hyper=battery(100),
            solarflow=battery(99, max_power=500),
        )
    )
    assert result.grid_export_allowed is True
    assert result.grid_w < 0


def test_mode_is_based_on_applied_flows():
    charging = simulate_cycle(
        TwinInput(
            house_load_w=200,
            grid_target_w=0,
            hyper_pv_w=900,
            solarflow_pv_w=0,
            hyper=battery(50),
            solarflow=battery(50),
        )
    )
    assert charging.mode == "charge"

    discharging = simulate_cycle(
        TwinInput(
            house_load_w=1000,
            grid_target_w=0,
            hyper_pv_w=0,
            solarflow_pv_w=0,
            hyper=battery(50),
            solarflow=battery(50),
        )
    )
    assert discharging.mode == "décharge"
