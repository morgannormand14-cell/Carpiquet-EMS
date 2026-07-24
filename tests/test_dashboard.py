from pathlib import Path

def test_dashboard_is_bundled():
    assert Path('dashboards/carpiquet_ems.yaml').exists()
    assert Path('custom_components/carpiquet_ems/dashboard/carpiquet_ems.yaml').exists()
