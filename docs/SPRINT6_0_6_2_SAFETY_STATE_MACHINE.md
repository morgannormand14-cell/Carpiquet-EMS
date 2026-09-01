# Sprint 6 — v0.6.2-alpha-sprint6

## Safety State Machine & Recovery Watchdog

v0.6.2 builds on the validated v0.6.1 Shadow Mode and introduces a persistent
runtime safety state machine before any future real-write adapter exists.

### States

- `SAFE_IDLE` — default Simulation state.
- `SHADOW_ACTIVE` — Shadow command may be exposed as `would_send_command`.
- `HOLD` — transient anomaly; validated Shadow outputs are gated to 0 W.
- `FAULT` — anomaly persisted beyond the escalation delay.
- `RECOVERY` — sources are healthy again but must remain stable before Shadow resumes.
- `ARMED_LOCKED` — Armed architecture state; real writes remain impossible.

### Timers

- HOLD to FAULT: 30 seconds by default.
- RECOVERY stabilization: 10 seconds by default.

A valid Shadow command is not re-authorized immediately after a fault. It must
pass through RECOVERY and stay healthy for the full stabilization interval.

### Reporting

Every sample now records state, reason, state duration, transition counters,
HOLD/FAULT/RECOVERY counters, last fault and remaining recovery/escalation time.
The raw command safety decision is retained separately from the final gated
command decision.

### Safety

- No Live mode.
- Armed remains locked.
- No Zendure write service calls.
- Home Assistant reload returns control mode to Simulation.

**Safety before performance. Always.**
