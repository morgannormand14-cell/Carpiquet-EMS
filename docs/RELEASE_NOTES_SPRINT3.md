# Carpiquet EMS v0.4.0-alpha — Normandy / Sprint 5

## Onboarding

Sprint 3 improves the installation and configuration experience while
preserving the simulation-only safety model.

### Added

- Home Assistant entity selectors in Config Flow
- Options Flow for post-install configuration
- Guided Premium Dashboard installer service
- Bundled dashboard template
- French UI strings
- Dashboard installation guide
- Sprint 3 validation checklist

### Safety

Carpiquet EMS remains 100% simulation-only. The integration never writes to:

- `number.hyper_2000_output_limit`
- `number.solarflow_2400_pro_output_limit`

### Tag

`v0.5.6-alpha-sprint5`
