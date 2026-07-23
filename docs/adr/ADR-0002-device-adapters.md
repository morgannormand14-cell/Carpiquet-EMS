# ADR-0002 — Device Adapter Pattern

## Status

Accepted

## Decision

Device-specific Home Assistant entities are normalised by adapters before entering the EMS core.

## Consequences

- the Decision Engine is device-independent;
- new hardware can be added without rewriting balancing logic;
- adapter validation becomes mandatory.
