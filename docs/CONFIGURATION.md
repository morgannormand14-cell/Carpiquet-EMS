# Configuration

## Current Reference Installation

| Function | Entity |
|---|---|
| Grid power | `sensor.shellypro3em_441d64748468_energy_meter_2_puissance` |
| Hyper SOC | `sensor.hyper_2000_electric_level` |
| Hyper PV | `sensor.hyper_2000_solar_input_power` |
| Hyper output limit | `number.hyper_2000_output_limit` |
| SolarFlow SOC | `sensor.solarflow_2400_pro_electric_level` |
| SolarFlow PV | `sensor.solarflow_2400_pro_solar_input_power` |
| SolarFlow output limit | `number.solarflow_2400_pro_output_limit` |

## Battery Parameters

- Hyper capacity: 3.84 kWh
- Hyper maximum output: 1200 W
- SolarFlow capacity: 5.28 kWh
- SolarFlow maximum output: 2400 W
- Minimum SOC: 10%
- Grid target: 0 W
- Deadband: 20 W

## Grid Sign

- Positive = import from EDF
- Negative = export to EDF
