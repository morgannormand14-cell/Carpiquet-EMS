from pathlib import Path

def test_complete_session_reset_present():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(encoding="utf-8")
    for token in (
        "self._perf_score_sum = 0.0",
        "self._zendure_score_sum = 0.0",
        "self._real_import_kwh = 0.0",
        "self._last_cycle_dt = None",
        "self._twin_prev_hyper_charge = 0.0",
    ):
        assert token in source

def test_interrupted_summary_is_rebuilt():
    source = Path("custom_components/carpiquet_ems/session_recorder.py").read_text(encoding="utf-8")
    assert "def _rebuild_summary" in source
    assert '"missing_data_intervals"' in source
    assert '"last_sample_timestamp"' in source
    assert '"summary": self._rebuild_summary(samples)' in source
