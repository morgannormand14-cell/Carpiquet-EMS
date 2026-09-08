from pathlib import Path


def test_v065_mapper_is_shadow_only():
    text = Path("custom_components/carpiquet_ems/entity_mapper.py").read_text()
    assert '"shadow_read_only"' in text
    assert '"legacy_v0.6.4"' in text
    assert "async_call" not in text


def test_coordinator_records_systems_without_engine_cutover():
    text = Path("custom_components/carpiquet_ems/coordinator.py").read_text()
    assert "build_shadow_systems" in text
    assert 'result_data["systems"]' in text
    assert '"mapper_parity_ready"' in text
