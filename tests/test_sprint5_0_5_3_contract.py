from pathlib import Path

def test_runtime_switch_does_not_update_config_entry():
    source = Path("custom_components/carpiquet_ems/switch.py").read_text(encoding="utf-8")
    assert "async_update_entry" not in source
    assert "async_set_automation_enabled" in source

def test_house_formula_includes_grid_inputs():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    assert "hyper_grid_input" in source
    assert "solar_grid_input" in source
    assert "- max(0.0, hyper_grid_input)" in source
    assert "- max(0.0, solar_grid_input)" in source

def test_report_platforms_exist():
    assert Path("custom_components/carpiquet_ems/select.py").exists()
    assert Path("custom_components/carpiquet_ems/button.py").exists()
