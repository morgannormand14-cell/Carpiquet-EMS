Carpiquet EMS v0.6.5-alpha.3.6
Normandy Sprint 7 — Step 2B — Initial Discovery Config Flow

Main changes:
- New installation asks only for the grid instantaneous power sensor
- Runs one read-only Zendure registry discovery during initial setup
- Shows a confirmation step before creating the Carpiquet config entry
- Excludes Zendure infrastructure devices such as Zendure Manager by hardware model catalogue
- Preserves legacy_v0.6.4 as sole EMS authority
- Preserves Generic Engine shadow_compare and all hard write locks
- Stores the confirmed discovery snapshot in the config entry for diagnostics/migration
- Removes the generated dashboard YAML file when the integration entry is removed

Expected real-installation regression gate:
- Hyper 2000: system
- SolarFlow 2400 Pro: system
- Zendure Manager: excluded infrastructure
- systems_count = 2
- batteries_count = 4

Important scope note:
- Initial installation confirmation is implemented.
- Manual Synchroniser button remains read-only/pending-validation in this alpha; a button cannot directly open a Home Assistant config-flow dialog. Inventory reconciliation UI will be wired through a dedicated HA flow in the next Step 2B sub-phase.
- The generated YAML dashboard file is removed on entry deletion, but an existing manual lovelace: declaration in configuration.yaml cannot be safely edited automatically by the integration.

Safety:
- No Zendure API/MQTT/HTTP write path added
- No periodic hardware discovery
- Real Writes Enabled remains false
- Command Write Locked remains true
- Adapter Write Locked remains true
