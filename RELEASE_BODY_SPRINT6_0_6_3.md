# Carpiquet EMS v0.6.3-alpha-sprint6 — Zendure Command Adapter (Locked)

This alpha prepares the final translation layer toward Zendure while keeping **all real writes physically/logically locked**.

## Added
- Zendure Command Adapter in DRY-RUN mode.
- Per-device prepared command, target, action and reason.
- Secondary ramp limiting.
- Deduplication when the observed setting is already within 5 W.
- `would_execute` diagnostics, separate from actual execution.
- Adapter sequence and timestamp telemetry.

## Corrected
- Hyper 2000 “Réglage Zendure observé” now reads the configured real Hyper output sensor, matching the sensor validated during the v0.6.2 72-hour test.

## Safety
- No `number.set_value`.
- No `async_set_value`.
- No Zendure service call.
- Adapter and command pipeline write locks remain `true`.
- Home Assistant restart still returns control mode to Simulation.

This is still an alpha Shadow validation release. **Do not use it as Live control.**

Safety before performance. Always.
