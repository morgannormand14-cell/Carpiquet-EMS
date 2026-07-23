# Carpiquet EMS

Energy Management System for Home Assistant, designed for a Zendure Hyper 2000 + SolarFlow 2400 Pro installation with a Shelly Pro 3EM grid meter.

## v0.1.1-alpha

This release is **simulation-only**. It reads Home Assistant entities and calculates theoretical battery discharge. It never writes to the Zendure output-limit entities.

### Current installation

- Grid: `sensor.shellypro3em_441d64748468_energy_meter_2_puissance`
- Hyper SOC: `sensor.hyper_2000_electric_level`
- Hyper PV: `sensor.hyper_2000_solar_input_power`
- Hyper output: `number.hyper_2000_output_limit`
- SolarFlow SOC: `sensor.solarflow_2400_pro_electric_level`
- SolarFlow PV: `sensor.solarflow_2400_pro_solar_input_power`
- SolarFlow output: `number.solarflow_2400_pro_output_limit`

### Battery configuration

- Hyper 2000: 3.84 kWh, 1200 W maximum
- SolarFlow 2400 Pro: 5.28 kWh, 2400 W maximum
- Minimum SOC: 10%
- Combined maximum: 3600 W

### Grid sign convention

- Positive Shelly value = import from EDF
- Negative Shelly value = export/injection to EDF

### Improvements

- Stable `sensor.carpiquet_ems_*` entity IDs.
- Strict minimum-SOC protection.
- Minimum SOC default 10%.
- PV monitoring.
- Simulated grid power.
- Detailed diagnostics.
- Tests for the observed real-world scenarios.
- No Zendure commands.

## Safety

This version is simulation-only. It does not call `number.set_value` on Zendure output-limit entities.

## Installation

Copy `custom_components/carpiquet_ems` into `/config/custom_components/carpiquet_ems`, restart Home Assistant, then add **Carpiquet EMS**.
