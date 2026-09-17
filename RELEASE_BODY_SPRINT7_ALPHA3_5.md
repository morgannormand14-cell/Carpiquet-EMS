Carpiquet EMS v0.6.5-alpha.3.5
Normandy Sprint 7 — Step 2B — Manual Zendure Discovery (Read Only)

Main changes:
- Adds a dedicated Zendure Device Discovery layer based on Home Assistant Device Registry and Entity Registry
- Detects Zendure top-level systems without hard-coded entity IDs
- Detects child batteries through Home Assistant device parent relationships
- Maps semantic Zendure entities from Entity Registry translation keys
- Introduces protocol_generation and control_profile metadata
- Renames the Dashboard regeneration button to "Synchroniser Carpiquet EMS"
- Manual synchronization runs Zendure discovery exactly once per button press
- Synchronization regenerates the Dynamic Dashboard after discovery
- Exposes discovery state, detected system count and detected battery count
- Keeps discovered inventory pending validation; no automatic hardware inventory change is applied

Discovery policy:
- Initial/config-flow discovery: reserved for a later Step 2B sub-phase
- Manual discovery: enabled through "Synchroniser Carpiquet EMS"
- Periodic hardware discovery: disabled
- Coordinator 2-second refresh never queries Device Registry for hardware discovery
- Temporary device unavailability is not interpreted as hardware removal

Safety / authority:
- Legacy v0.6.4 remains sole EMS authority
- Generic Engine remains shadow_compare only
- Generic Authority remains false
- Real Zendure writes remain disabled
- Command Write Locked remains unchanged
- Adapter Write Locked remains unchanged
- Discovery reads Home Assistant registries only
- No Zendure API/MQTT/HTTP discovery request is sent by Carpiquet EMS
- No discovered inventory is committed automatically

Validation before package:
- Baseline source: user-provided v0.6.5-alpha.3.4 Sprint 7 Step 1 package
- Version manifest/const consistency: PASS
- Python compilation: PASS
- Static discovery policy check: PASS
- No periodic call to discover_zendure_inventory: PASS
- No service/entity write in zendure_discovery.py: PASS
- No packaged __pycache__ / .pyc: PASS

Real Home Assistant validation: PENDING
