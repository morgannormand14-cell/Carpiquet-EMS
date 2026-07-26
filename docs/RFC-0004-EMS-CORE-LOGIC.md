# RFC-0004 — EMS Core Logic
## Status
Accepted for Sprint 4.
## Objective
Build a deterministic and diagnosable EMS simulation core without enabling real device control.
## Rules
1. Grid error drives the discharge request.
2. Deadband filters small errors.
3. Unavailable batteries are excluded.
4. Minimum SOC is a hard reserve.
5. Maximum device power is a hard ceiling.
6. Available energy above reserve weights the allocation.
7. A per-cycle ramp limiter smooths simulated output.
8. The engine exposes limitation reason and unserved demand.
9. No Zendure write is permitted in Sprint 4.
## Dispatch mode
`energy_weighted_balanced`
