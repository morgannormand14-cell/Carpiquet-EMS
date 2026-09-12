# Carpiquet EMS v0.6.5-alpha.3 — Normandy Sprint 6 — Generic 1–5 System Energy Engine

Phase A of the Sprint 6 multi-system migration.

## New: Generic Energy Engine
- New `generic_energy_engine.py` independent of Hyper/SolarFlow product names.
- Supports 1 to 5 normalized systems.
- Energy-Aware discharge based on usable energy above each system's own minimum SOC.
- Per-system inverter caps, energy limits, ramping and deterministic residual redistribution.

## Dual-engine Shadow comparison
The generic engine runs in parallel with the validated v0.6.4 legacy twin. It has **no command authority**.
Each recorded cycle now includes generic allocations and per-system/total deltas against the legacy discharge allocation.

## Safety
- Legacy v0.6.4 remains sole authority.
- Zendure real writes remain locked.
- Mapper and Control Profiles remain read-only.
- No change to Safety Pipeline or Command Adapter authority.

## Validation goal
Demonstrate two-system parity on the real Shadow workload before any future authority migration, while establishing the N-system architecture needed for 1–5 Zendure systems.
