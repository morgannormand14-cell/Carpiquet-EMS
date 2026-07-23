# RFC-0002 — Premium Dashboard

## Status

Implemented for Sprint 2 validation.

## Objective

Provide a responsive, dependency-free Home Assistant dashboard that explains the installation state in less than ten seconds.

## Principles

- Native Home Assistant cards only.
- Mobile-first layout.
- Simulation status always visible.
- Critical health information above the fold.
- Identical visual structure for both battery systems.
- No colour-only communication.

## Views

1. Cockpit
2. EMS Health Center
3. History

## Runtime Additions

Sprint 2 adds:

- system status sensor;
- health score sensor;
- grid-meter health binary sensor;
- Hyper health binary sensor;
- SolarFlow health binary sensor.

## Out of Scope

- automatic dashboard installation;
- real-control interface;
- custom frontend panel;
- third-party Lovelace cards.
