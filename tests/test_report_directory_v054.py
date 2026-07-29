from pathlib import Path


def test_report_directory_creation_is_idempotent():
    source = Path(
        "custom_components/carpiquet_ems/coordinator.py"
    ).read_text(encoding="utf-8")
    assert "mkdir(parents=True, exist_ok=True)" in source


def test_visible_deadband_wording_is_updated():
    source = Path(
        "custom_components/carpiquet_ems/automation_engine.py"
    ).read_text(encoding="utf-8")
    assert '"inside_deadband": "Dans la plage de lissage"' in source
    assert '"inside_deadband": "Dans la bande morte"' not in source
