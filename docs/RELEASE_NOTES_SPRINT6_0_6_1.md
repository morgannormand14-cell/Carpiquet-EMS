# Carpiquet EMS v0.6.1-alpha-sprint6

## Corrective: Shadow source freshness

- Replaced the generic maximum source-age guard.
- Shelly grid freshness is now monitored independently.
- Stable Zendure SOC/PV/output values no longer trigger a false stale-data rejection.
- Added per-source age diagnostics.
- Added explicit watchdog states and reasons.
- Added `last_reported` support with `last_updated` fallback.
- Added numeric availability validation for command sources.
- Fixed initialization guard so a legitimate 0% SOC is accepted.
- Shadow / Armed remain write-locked.
- No Live mode.
- No real Zendure writes.

**Safety before performance. Always.**
