# GitHub Upload Plan

Upload the package contents at the repository root while preserving paths.

## Replace

- `custom_components/carpiquet_ems/__init__.py`
- `custom_components/carpiquet_ems/config_flow.py`
- `custom_components/carpiquet_ems/const.py`
- `custom_components/carpiquet_ems/manifest.json`
- `custom_components/carpiquet_ems/strings.json`
- `custom_components/carpiquet_ems/translations/fr.json`
- `dashboards/carpiquet_ems.yaml`
- `docs/INSTALLATION.md`

## Add

- `custom_components/carpiquet_ems/dashboard.py`
- `custom_components/carpiquet_ems/dashboard/carpiquet_ems.yaml`
- `custom_components/carpiquet_ems/services.yaml`
- `docs/RFC-0003-ONBOARDING.md`
- `docs/DASHBOARD_INSTALLATION.md`
- `docs/SPRINT3_VALIDATION.md`
- `docs/RELEASE_NOTES_SPRINT3.md`

## Preserve from Sprint 2

Do not delete `sensor.py`, `binary_sensor.py`, `number.py`, `switch.py`,
`coordinator.py`, tests, assets, or existing governance documents.
