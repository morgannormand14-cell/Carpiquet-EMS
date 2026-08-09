# Sprint 6 — v0.6.0-alpha-sprint6

## Command Pipeline & Shadow Mode

v0.6.0 introduces a separate command pipeline between the Carpiquet EMS
energy engine and any future Zendure write adapter.

Pipeline:

1. Sensors and dynamic limits
2. Digital twin
3. Requested command
4. Safety validation
5. Validated command
6. Shadow comparison
7. Write adapter — intentionally absent / locked in v0.6.0

## Control modes

- **Simulation** — default after every Home Assistant reload.
- **Shadow** — calculates the exact validated command that would be sent.
- **Armed** — exposes the future armed state, but writes remain hard locked.
- There is no Live mode in v0.6.0.

## Safety rules

The command is rejected when:
- engine initialization is incomplete;
- the grid meter is unavailable;
- either Zendure system is unavailable;
- fallback data is active while fallback is forbidden;
- source data is older than the safety window.

Power is clamped to device limits. At or below the minimum SOC, the validated
home-output command cannot exceed the available direct PV power.

## Important

**No Home Assistant service call or number.set_value command is present in
the v0.6.0 command pipeline.**

Safety before performance. Always.
