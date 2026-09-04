# v0.6.3-alpha-sprint6 — Zendure Command Adapter (Locked)

- Adds a dry-run Zendure Command Adapter.
- Adds secondary ramp limiting and command deduplication.
- Adds explicit adapter target/action/reason/would-execute diagnostics.
- Keeps a hard write lock: zero real Zendure writes.
- Corrects Hyper observed output telemetry to the real Hyper output sensor.
- Preserves the v0.6.2 Safety State Machine and v0.6.1 freshness watchdog.
