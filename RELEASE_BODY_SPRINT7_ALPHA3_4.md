Carpiquet EMS v0.6.5-alpha.3.4
Normandy Sprint 7 — Step 1 — Runtime Architecture Diagnostics

This pre-release starts Sprint 7 from the validated Sprint 6 alpha.3.3 baseline.

Main changes:
- Exposes Engine Authority in Home Assistant
- Exposes Generic Engine Mode in Home Assistant
- Exposes Generic Authority as a binary diagnostic
- Exposes Real Writes Enabled as a binary diagnostic
- Exposes Mapper Systems Count
- Exposes Mapper Available Systems Count
- Exposes Mapper Ready
- Adds a dedicated Runtime Architecture card to the dynamic Dashboard

Expected validated baseline values:
- Engine Authority: legacy_v0.6.4
- Generic Engine Mode: shadow_compare
- Generic Authority: false
- Real Writes Enabled: false
- Command Write Locked: true
- Adapter Write Locked: true
- Mapper Systems Count: 2 on the current installation
- Mapper Ready: true when required mapped telemetry is available

Safety / scope:
- No Legacy EMS algorithm change
- No Generic Energy Engine algorithm change
- No Safety State Machine change
- No Command Pipeline behavior change
- No Zendure Command Adapter behavior change
- Legacy v0.6.4 remains sole EMS authority
- Generic Engine remains Shadow Compare only
- Real Zendure writes remain disabled / locked

Validation status:
- Source package SHA matches validated alpha.3.3 baseline: PASS
- Python compileall: PASS
- Static Sprint 7 diagnostics contract: PASS
- No __pycache__ / .pyc in package: PASS
- Full pytest suite not runnable in build sandbox because Home Assistant dependency voluptuous is unavailable
- Real Home Assistant validation: PENDING
