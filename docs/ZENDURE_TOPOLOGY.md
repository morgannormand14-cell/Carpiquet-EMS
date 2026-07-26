# Zendure Topology — Sprint 4

Carpiquet EMS uses:
- `sensor.hyper_2000_pack_num`
- `sensor.solarflow_2400_pro_pack_num`

to determine the expected physical battery count.

The installer then requests only battery type and serial number. Entity IDs are derived from the Zendure naming convention and validated before the configuration is accepted.

Example mappings:
- `AB2000X` + `90400` → `sensor.ab2000x_90400_soc_level`
- `I2400` + `00545` → `sensor.i2400_00545_soc_level`
- `AB3000L` + `03090` → `sensor.ab3000l_03090_soc_level`

The generated dashboard file contains one native Home Assistant entity card per configured physical battery.
