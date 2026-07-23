# ADR-0001 — Simulation First

## Status

Accepted

## Decision

All control logic is validated in simulation before it may send commands to real equipment.

## Consequences

- slower progression toward real control;
- safer testing;
- comparable simulation and production pipelines;
- easier regression testing.
