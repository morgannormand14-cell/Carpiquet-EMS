import json
from pathlib import Path

def test_manifest_version():
    manifest = json.loads(Path('custom_components/carpiquet_ems/manifest.json').read_text())
    assert manifest['version'] == '0.5.1-alpha-sprint5'
    assert manifest['config_flow'] is True
