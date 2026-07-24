# RFC-0003 — Guided Onboarding

## Status

Accepted for Sprint 3.

## Objective

Reduce the number of manual steps between HACS installation and a working
Carpiquet EMS cockpit.

## Decisions

1. Use Home Assistant entity selectors in the Config Flow.
2. Add an Options Flow so configuration can be edited without deleting the entry.
3. Bundle the official dashboard inside the integration.
4. Expose `carpiquet_ems.install_dashboard` to copy the dashboard safely.
5. Never edit `configuration.yaml` automatically.
6. Keep simulation mode permanently enforced in this alpha milestone.

## Rationale

Automatic modification of Home Assistant configuration would be intrusive and
fragile. Sprint 3 therefore provides a guided, reversible installation path
using a Home Assistant service and explicit user confirmation.
