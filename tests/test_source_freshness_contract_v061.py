from pathlib import Path


def test_coordinator_no_longer_uses_max_age_across_all_sources():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    assert "_max_source_age_seconds" not in source
    assert "_source_age_seconds" in source
    assert "grid_source_fresh" in source
    assert "grid_strict_other_sources_availability" in source


def test_stable_zendure_sources_are_availability_checked_not_age_gated():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    assert "hyper_command_sources_ok" in source
    assert "solar_command_sources_ok" in source
    assert "hyper_soc_source_age" in source
    assert "solar_pv_source_age" in source


def test_zero_soc_initialization_is_not_rejected_as_zero():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    assert 'return False, "SOC invalide ou nul"' not in source
    assert "_source_numeric_available(entity_id, 0.0, 100.0)" in source
