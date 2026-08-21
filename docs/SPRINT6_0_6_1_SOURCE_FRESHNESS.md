# Sprint 6 — v0.6.1-alpha-sprint6

## Source Freshness & Safety Watchdog

v0.6.0 proved that the Shadow command pipeline works, but its freshness guard
used the maximum `last_updated` age across all sources. Stable Zendure values
such as PV=0 W could therefore be interpreted as stale for hours.

v0.6.1 replaces that model.

### Freshness policy

**Strict freshness**
- Shelly grid power is command-critical.
- The watchdog requires the grid source to be available and recently reported.
- Default maximum age: 60 seconds.

**Availability / numeric validity**
- Hyper SOC
- SolarFlow SOC
- Hyper PV
- SolarFlow PV
- Hyper real output
- SolarFlow real output

These sources must remain available and numeric, but a stable value is no
longer rejected simply because it has not changed.

`last_reported` is used when supported by Home Assistant; `last_updated` is
the compatibility fallback.

### Per-source diagnostics

The integration now exposes the age of every command source separately and
records those values in simulation reports.

### Watchdog states

- OK
- INITIALIZING
- GRID_UNAVAILABLE
- GRID_STALE
- HYPER_UNAVAILABLE
- SOLARFLOW_UNAVAILABLE
- FALLBACK_BLOCKED

### Additional corrective

A legitimate numeric 0% SOC is now accepted by the initialization guard.
`unknown` / `unavailable` states remain rejected.

### Safety

There is still no Live mode and no Zendure write path in v0.6.1.

**Safety before performance. Always.**
