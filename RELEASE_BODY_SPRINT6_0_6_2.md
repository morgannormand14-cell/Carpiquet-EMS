# Carpiquet EMS v0.6.2-alpha-sprint6 — Safety State Machine & Recovery Watchdog

> **Every watt counts.**  
> Intelligent energy management for Zendure.  
> Designed with ❤️ in Normandy.  
> Engineered for reliability. Built for Home Assistant.

v0.6.2 strengthens the validated Sprint 6 Shadow pipeline with a dedicated
safety state machine.

## New safety states

`SAFE_IDLE` → `RECOVERY` → `SHADOW_ACTIVE`

A transient anomaly moves the controller to `HOLD`. If it persists for 30 s,
it escalates to `FAULT`. When sources return, the controller enters `RECOVERY`
for 10 s before Shadow commands can be authorized again.

During `HOLD`, `FAULT` and `RECOVERY`:

- validated Shadow output = 0 W;
- `would_send_command = false`;
- the raw command calculation remains visible for diagnostics.

## Diagnostics

The dashboard and reports now expose the current safety state, reason, duration,
transition counters, last fault, HOLD/FAULT/RECOVERY counts and recovery timers.

## Safety

No Live mode exists in this release. Armed remains hard locked. No real Zendure
write path is present.

> **Safety before performance. Always.**

Tag: `v0.6.2-alpha-sprint6`  
Pre-release: **Yes**
