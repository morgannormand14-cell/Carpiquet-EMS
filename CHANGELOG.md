# Changelog

## v0.5.0-alpha — Sprint 5 Automation Engine

- Added deterministic automation state machine.
- Added disabled / safe_hold / idle / discharge states.
- Added grid, battery and fallback safety gates.
- Added configurable minimum state hold.
- Added automation sensors and safety binary sensor.
- Added functional Automation Engine simulation switch.
- Added Automation dashboard view.
- Preserved simulation-only safety boundary.

## v0.4.3-alpha — Sprint 5 Config Flow hotfix

- Fixed first-step Config Flow submission reporting all fields as extra keys.
- Replaced reconstructed schema with one stable explicit schema.
- Suggested values now use Home Assistant's schema helper.
- Battery serial validation moved to the flow logic.
- Dashboard and onboarding improvements from v0.4.2 preserved.

## v0.4.2-alpha — Sprint 5 corrective release

- Battery type dropdown for AB2000X / AB3000L / I2400.
- Five-digit serial validation with leading-zero support.
- Corrected dashboard entity IDs.
- Simplified dashboard labels in Cockpit, Health Center and Zendure views.
- Simulation-only safety unchanged.

## v0.4.1-alpha — Sprint 5 dynamic Zendure revision

- Dynamic capacities, max powers and min/max SOC sourced from Zendure entities.
- Persistent self-updating fallback cache.
- LIVE / FALLBACK ACTIF diagnostics.
- Battery topology based on pack_num.
- Automatic type + serial BMS entity mapping.
- Cockpit synthesis and new Zendure dashboard view.
- Fixes Sprint 5 Config Flow schema regression.

## v0.4.0-alpha — Normandy / Sprint 5

### Added

- entity selectors in Config Flow;
- duplicate-entry protection;
- Options Flow;
- guided dashboard installation service;
- bundled Premium Dashboard;
- French strings and service descriptions;
- Sprint 3 onboarding documentation and validation checklist.

### Safety

Runtime remains simulation-only. No Zendure output-limit entity is written.

## v0.3.0-alpha — Normandy / Sprint 2

- Premium Cockpit dashboard;
- EMS Health Center;
- native history views;
- health score and system status;
- health binary sensors.

## v0.3.0-alpha — Normandy / Sprint 1

- project foundation, governance, architecture and branding.
