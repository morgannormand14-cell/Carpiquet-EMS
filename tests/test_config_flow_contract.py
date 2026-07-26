from pathlib import Path

EXPECTED_MAIN_KEYS = [
    "CONF_GRID_POWER_ENTITY",
    "CONF_HYPER_SOC_ENTITY",
    "CONF_HYPER_PV_ENTITY",
    "CONF_HYPER_OUTPUT_ENTITY",
    "CONF_SOLARFLOW_SOC_ENTITY",
    "CONF_SOLARFLOW_PV_ENTITY",
    "CONF_SOLARFLOW_OUTPUT_ENTITY",
    "CONF_HYPER_CAPACITY_ENTITY",
    "CONF_SOLARFLOW_CAPACITY_ENTITY",
    "CONF_HYPER_MAX_POWER_ENTITY",
    "CONF_SOLARFLOW_MAX_POWER_ENTITY",
    "CONF_HYPER_MIN_SOC_ENTITY",
    "CONF_HYPER_MAX_SOC_ENTITY",
    "CONF_SOLARFLOW_MIN_SOC_ENTITY",
    "CONF_SOLARFLOW_MAX_SOC_ENTITY",
    "CONF_GRID_TARGET",
    "CONF_GRID_DEADBAND",
    "CONF_RAMP_LIMIT_W",
]

def test_main_schema_contract_contains_all_fields():
    source = Path("custom_components/carpiquet_ems/config_flow.py").read_text(encoding="utf-8")
    block = source.split("MAIN_SCHEMA = vol.Schema(", 1)[1].split("def _schema_with_values", 1)[0]
    for key in EXPECTED_MAIN_KEYS:
        assert f"vol.Required({key})" in block

def test_config_flow_uses_suggested_values_helper():
    source = Path("custom_components/carpiquet_ems/config_flow.py").read_text(encoding="utf-8")
    assert "add_suggested_values_to_schema" in source
    assert 're.fullmatch(r"\\d{5}", serial)' in source
