# Carpiquet EMS v0.6.5-alpha — Dynamic Entity Mapper / systems[] Shadow

Phase 1 of the multi-system architecture.

- Adds a read-only Entity Mapper.
- Normalizes the configured Hyper 2000 and SolarFlow 2400 Pro into `systems[]`.
- Exposes mapper availability and parity diagnostics in coordinator state and simulation logs.
- Keeps the validated v0.6.4 Energy-Aware engine as the sole command authority.
- Does not enable real Zendure writes; the existing Shadow / DRY_RUN safety architecture is unchanged.
- Prepares the later 1–5 Zendure-system engine generalization only after mapping parity is validated.
