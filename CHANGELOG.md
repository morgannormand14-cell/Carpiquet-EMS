# Changelog

## v0.6.0-alpha-sprint6 — Command Pipeline & Shadow Mode

- Opened Sprint 6.
- Added isolated command pipeline and safety validation.
- Added Simulation, Shadow and Armed runtime control modes.
- Added hard write lock; no real Zendure write path exists.
- Added requested/validated command telemetry and Zendure-setting comparison.
- Added source-age safety guard and shadow counters.
- Added command fields to simulation reports and dashboard.


## v0.6.0-alpha-sprint6 — Corrective finale Sprint 5

- Reset all session performance and energy accumulators.
- Rebuild complete summaries for orphaned/interrupted sessions.
- Add collection-gap statistics to recovered reports.
- Preserve initialization guard and atomic finalization.

## v0.6.0-alpha-sprint6 — Sprint 5 release

- Added guarded engine initialization.
- Wait up to 30 seconds for valid SOC and essential entity data.
- Refuse zero or unavailable SOC values.
- Start the simulation session only after a valid real snapshot.
- Return the runtime engine to OFF when initialization fails.
- Expose initialization state, readiness and error diagnostics.
- Keep atomic report finalization from v0.5.6.

## v0.5.6-alpha — Atomic session finalization

- Disable the runtime engine before session finalization.
- Reject samples after the stop boundary.
- Add a thread-safe recorder lock.
- Capture `ended_at` after the last accepted sample.
- Write final reports atomically through a temporary file.
- Preserve JSONL recovery data when finalization fails.
- Add recording/finalization/error diagnostics.
- Fix the dashboard installation notification path.

## v0.5.5-alpha — Sprint 5 dynamic twin

- Dynamic digital twin with deadband, ramping and previous-command memory.
- Energy-limited charge/discharge based on virtual SOC.
- Progressive performance scoring and session averages.
- Cumulative real/sim import/export and PV storage/curtailment metrics.
- Negative reconstructed house load guardrail with raw diagnostic value.
- Home Assistant report button notification API fixed.

## v0.5.4-alpha — Sprint 5 solar priority and export policy

- Fixed report preparation when the destination directory already exists.
- Replaced the remaining visible deadband wording with Plage de lissage.
- Full-battery systems' PV now supplies the house first.
- Non-full systems preserve PV for charging until additional house supply is required.
- EDF export is blocked when all batteries are full.
- Non-storable surplus is reported as curtailed PV.
- EDF export is automatically re-enabled when at least one battery falls below maximum SOC.
- Added detailed solar-flow and export-policy diagnostics.

## v0.5.3-alpha — Sprint 5 session/report corrective

- Automation switch moved to runtime state; no Config Entry reload on ON/OFF.
- Recorder watchdog added.
- Session finalized on integration unload.
- House-load formula now subtracts Hyper/SolarFlow AC grid inputs.
- Simulation report selector and prepare-download button added.
- UI vocabulary changed to État du moteur / Plage de lissage.

## v0.5.2-alpha — Sprint 5 corrective + sessions

- Stable technical entity IDs and dashboard alignment.
- Health / automation safety entities corrected.
- Visible states fully localized in French.
- Automation OFF→ON starts a fresh simulation session.
- Previous session is finalized on OFF.
- One JSON file per simulation session.
- Virtual battery state, cycles and performance reset at session start.

## v0.5.1-alpha — Sprint 5 Digital Twin

- Interface francisée.
- Garde-fou sécurité corrigé.
- Jumeau numérique bidirectionnel.
- Reconstitution de la consommation maison.
- Stockage local prioritaire puis transfert inter-systèmes du surplus PV.
- Comparaison réseau réel / simulé et indice de performance.
- Simulation uniquement conservée.

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
