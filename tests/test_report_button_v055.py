from pathlib import Path

def test_report_button_uses_official_notification_api():
    s=Path('custom_components/carpiquet_ems/button.py').read_text(encoding='utf-8')
    assert 'from homeassistant.components import persistent_notification' in s
    assert 'self.hass.components' not in s

def test_report_preparation_is_idempotent():
    s=Path('custom_components/carpiquet_ems/coordinator.py').read_text(encoding='utf-8')
    assert 'mkdir(parents=True, exist_ok=True)' in s
