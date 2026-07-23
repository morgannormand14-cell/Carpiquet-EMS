# ADR-0003 — Safety Engine Priority

## Status

Accepted

## Decision

Safety constraints override optimisation decisions and user performance targets.

## Consequences

- unsafe commands are blocked;
- performance may be reduced during degraded conditions;
- safety behaviour must be independently testable.
