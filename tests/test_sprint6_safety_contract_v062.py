from pathlib import Path


def test_no_real_write_path():
    base = Path("custom_components/carpiquet_ems")
    text = "\n".join(p.read_text(encoding="utf-8") for p in base.glob("*.py"))
    assert "async_set_value" not in text
    assert 'services.async_call("number"' not in text
    assert "number.set_value" not in text


def test_coordinator_gates_shadow_until_authorized():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    assert "self._safety_state_machine.update" in source
    assert "not safety_state.shadow_authorized" in source
    assert "validated=CommandRequest(0.0, 0.0, 0.0, 0.0)" in source
    assert "ATTR_RAW_COMMAND_SAFETY_OK" in source


def test_reload_returns_to_simulation():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    assert "self._control_mode = CONTROL_MODE_SIMULATION" in source
