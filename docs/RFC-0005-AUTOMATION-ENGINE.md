# RFC-0005 — Automation Engine

## Status
Accepted for Sprint 5.

## Goal
Introduce a deterministic automation state machine between the EMS calculation and any future actuator layer.

## Sprint 5 states
- `disabled`
- `safe_hold`
- `idle`
- `discharge`

## Safety gates
The engine enters `safe_hold` when:
- the grid meter is unavailable;
- no configured physical battery is active;
- fallback data is active while fallback automation is disallowed.

## Debounce
Normal state transitions respect a configurable minimum hold duration.
Safety transitions bypass the hold timer.

## Output
The engine produces:
- state;
- reason;
- requested simulated power;
- safety-gate state;
- cycle counter;
- last transition timestamp;
- remaining hold time.

## Critical boundary
Sprint 5 remains 100% simulation-only.

The automation engine is a decision layer only. It does not call Zendure control services and never writes output-limit entities.
