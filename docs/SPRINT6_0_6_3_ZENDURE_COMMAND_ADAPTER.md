# Sprint 6.3 — Zendure Command Adapter (Locked)

v0.6.3-alpha introduces the translation layer between the validated Carpiquet EMS command and a future Zendure executor.

## Safety contract

**No real Zendure write exists in this release.** The adapter only builds DRY-RUN command objects. `write_locked` is hard-coded to `true`; no Home Assistant `number.set_value`/`async_set_value` call is present.

Pipeline: `Energy Engine → Safety Controller → Safety State Machine → Zendure Command Adapter (DRY-RUN) → [WRITE LOCK]`.

The adapter adds a secondary ramp limiter, command deduplication against the observed setting, explicit target mapping, per-device action/reason telemetry and would-execute telemetry.

The Hyper observed-setting diagnostic is corrected to use the configured real Hyper output sensor (`sensor.hyper_2000_output_home_power` in the validated installation), addressing the v0.6.2 observation issue.

**Safety before performance. Always.**
