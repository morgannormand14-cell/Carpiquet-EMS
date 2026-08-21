# Carpiquet EMS v0.6.1-alpha-sprint6 — Source Freshness & Safety Watchdog

> **Every watt counts.**  
> Intelligent energy management for Zendure.  
> Designed with ❤️ in Normandy.  
> Engineered for reliability. Built for Home Assistant.

v0.6.1 is the first corrective release of Sprint 6.

The v0.6.0 Shadow report showed that the command pipeline itself was working,
but 39,595 of 39,792 cycles were rejected because stable Zendure values were
incorrectly considered "too old".

## Corrected freshness model

Carpiquet EMS now separates **source availability** from **value-change age**.

The Shelly grid meter remains strictly monitored because it is the
command-critical measurement used to balance the house.

Zendure SOC, PV and output values must remain available and numeric, but a
stable value such as `0 W` PV overnight no longer causes a false rejection.

## New Safety Watchdog diagnostics

- independent grid freshness state;
- per-source age values;
- explicit watchdog state;
- precise safety reason;
- source-freshness model recorded in JSON reports.

## Home Assistant compatibility

`last_reported` is preferred when available. On older Home Assistant versions,
Carpiquet EMS falls back to `last_updated`.

## Initialization corrective

A legitimate numeric `0%` SOC is now accepted. `unknown`, `unavailable` or
non-numeric SOC values remain rejected.

## Safety

- Shadow Mode remains observation-only.
- Armed remains hard locked.
- No Live mode exists.
- No real Zendure command is sent.

> **Safety before performance. Always.**

Tag: `v0.6.1-alpha-sprint6`  
Pre-release: **Yes**
