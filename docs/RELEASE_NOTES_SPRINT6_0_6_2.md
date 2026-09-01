# Carpiquet EMS v0.6.2-alpha-sprint6

## Safety State Machine & Recovery Watchdog

- Added SAFE_IDLE / SHADOW_ACTIVE / HOLD / FAULT / RECOVERY / ARMED_LOCKED.
- Added 30 s HOLD-to-FAULT escalation timer.
- Added 10 s recovery stabilization timer.
- Shadow commands are gated to 0 W during HOLD, FAULT and RECOVERY.
- Added raw-vs-final command safety diagnostics.
- Added transition, HOLD, FAULT and RECOVERY counters.
- Added state-machine telemetry to JSON reports and dashboard.
- Preserved v0.6.1 source-freshness behavior.
- No Live mode and no real Zendure writes.

**Safety before performance. Always.**
