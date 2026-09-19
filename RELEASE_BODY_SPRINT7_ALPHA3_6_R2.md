Carpiquet EMS v0.6.5-alpha.3.6 r2
Normandy Sprint 7 — Step 2B — Home Assistant Registry Iteration Fix

Main correction:
- Fixes the alpha.3.6-r1 runtime crash in Zendure discovery on Home Assistant 2026.9.x.
- Device Registry is now iterated through the public read-only registry.devices collection.
- Entity Registry keeps its supported registry.entries mapping iteration path.
- Keeps the French inventory preview introduced by r1.
- Keeps Zendure infrastructure classification so Zendure Manager does not enter systems[].

Expected real-installation regression gate:
- Hyper 2000: system
- SolarFlow 2400 Pro: system
- Zendure Manager: infrastructure ignored
- systems_count = 2
- batteries_count = 4

Safety:
- Legacy v0.6.4 remains sole EMS authority
- Generic Engine remains shadow_compare
- Generic Authority remains false
- Real Zendure writes remain disabled
- Command Write Locked remains true
- Adapter Write Locked remains true
- No periodic hardware discovery

Validation before package:
- Python compilation: PASS
- JSON parsing: PASS
- r1 invalid DeviceRegistry.values() call removed: PASS
- Device Registry public collection iteration present: PASS
- No packaged __pycache__ / .pyc: PASS
- Real Home Assistant validation: PENDING
