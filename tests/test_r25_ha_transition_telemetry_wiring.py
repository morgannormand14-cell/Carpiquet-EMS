"""Offline guard for HA pack telemetry diagnostic wiring."""
from pathlib import Path


def test_ha_telemetry_wiring_does_not_claim_dispatch_or_confirmation():
    source = (Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/coordinator.py").read_text()
    assert 'hyper_pack_entity = self._state("sensor.hyper_2000_pack_state")' in source
    assert 'solar_pack_entity = self._state("sensor.solarflow_2400_pro_pack_state")' in source
    assert '"last_updated": changed.isoformat() if changed is not None else None' in source
    assert '"dispatch_registered": False' in source
    assert '"confirmation_state": "NOT_TRACKED"' in source
    assert '"r25_transition_telemetry": self._r25_transition_telemetry' in source
    assert '"r25_pack_transition_execution": "LOCKED_SIMULATION_ONLY"' in source
