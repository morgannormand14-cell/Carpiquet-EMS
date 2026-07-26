from custom_components.carpiquet_ems.topology import build_battery_entities, battery_prefix, valid_numeric

def test_ab2000x_mapping():
    entities = build_battery_entities("AB2000X", "90400")
    assert entities["soc_level"] == "sensor.ab2000x_90400_soc_level"
    assert entities["delta_voltage"] == "sensor.ab2000x_90400_delta_voltage"

def test_leading_zero_serial_is_preserved():
    assert battery_prefix("I2400", "00545") == "i2400_00545"

def test_ab3000l_mapping():
    entities = build_battery_entities("AB3000L", "03090")
    assert entities["power"] == "sensor.ab3000l_03090_power"

def test_numeric_validation():
    assert valid_numeric(3.84, 0.1, 100)
    assert not valid_numeric("unavailable", 0, 100)
    assert not valid_numeric(-1, 0, 100)
