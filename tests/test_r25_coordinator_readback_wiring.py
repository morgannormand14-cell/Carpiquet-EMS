"""Static integration guard: expose actual HTTP feedback without claiming pack transition."""
from pathlib import Path


def test_zensdk_feedback_wired_to_real_executor_result():
    source = (Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/coordinator.py").read_text()
    assert '"r25_http_setpoint_feedback"' in source
    for field in ("requested_w", "observed_w", "verified", "zero_verified", "error"):
        assert "self._r25_last_result." + field in source
    assert '"pack_transition_confirmed": False' in source
    assert "self._r25_last_result = await self._r25_session.apply(" in source
