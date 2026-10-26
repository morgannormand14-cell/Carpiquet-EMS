"""Contract checks for R25 configurable pack-state mapping (no hardware writes)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems"


def test_pack_state_defaults_and_option_selectors():
    constants = (ROOT / "const.py").read_text()
    flow = (ROOT / "config_flow.py").read_text()
    for key in ("CONF_HYPER_PACK_STATE_ENTITY", "CONF_SOLARFLOW_PACK_STATE_ENTITY"):
        assert key in constants
        assert "vol.Required(" + key in flow
    assert 'DEFAULT_HYPER_PACK_STATE_ENTITY = "sensor.hyper_2000_pack_state"' in constants
    assert 'DEFAULT_SOLARFLOW_PACK_STATE_ENTITY = "sensor.solarflow_2400_pro_pack_state"' in constants


def test_coordinator_uses_mapping_and_retains_fail_closed():
    source = (ROOT / "coordinator.py").read_text()
    assert "self._state(self.config.get(CONF_HYPER_PACK_STATE_ENTITY, DEFAULT_HYPER_PACK_STATE_ENTITY))" in source
    assert "self._state(self.config.get(CONF_SOLARFLOW_PACK_STATE_ENTITY, DEFAULT_SOLARFLOW_PACK_STATE_ENTITY))" in source
    assert "hyper_ok = hyper_ok and hyper_pack.eligible" in source
    assert "solar_ok = solar_ok and solar_pack.eligible" in source
    assert 'self._state("sensor.hyper_2000_pack_state")' not in source
    assert 'self._state("sensor.solarflow_2400_pro_pack_state")' not in source
