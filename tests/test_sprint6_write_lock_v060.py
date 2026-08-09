from pathlib import Path


def test_no_real_number_write_path():
    base = Path("custom_components/carpiquet_ems")
    text = "\n".join(p.read_text(encoding="utf-8") for p in base.glob("*.py"))
    assert "async_set_value" not in text
    assert 'services.async_call("number"' not in text
    assert "number.set_value" not in text


def test_control_mode_resets_to_simulation():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    assert "self._control_mode = CONTROL_MODE_SIMULATION" in source
