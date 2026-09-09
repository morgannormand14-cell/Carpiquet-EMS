# Carpiquet EMS v0.6.5-alpha.2 — Parity Validated & Control Profiles

## Entity Mapper parity officially validated

The v0.6.5-alpha.1 Shadow reference session `SIM-20260908-221137` ran for 41,829 cycles (~23 h 19 min).
Semantic parity comparisons showed zero differences for PV, measured home output and grid input on both Hyper 2000 and SolarFlow 2400 Pro.

The mapper now exposes `parity_evaluated: true` and `parity_ready: true` whenever the normalized mapping itself is available. The validated reference session is recorded in diagnostics.

`command_limit_w` is deliberately excluded from semantic parity because the two Zendure product generations do not expose/use that control value equivalently in the observed setup.

## Control profiles / capabilities

Each normalized `systems[]` entry now carries read-only control metadata:

- Hyper 2000: `control_profile: legacy_hyper`
- SolarFlow 2400 Pro: `control_profile: zensdk_generation`

Capabilities explicitly describe command-limit semantics, measured home output, grid-input telemetry, native SOC reference and Shadow-only control status.

This is metadata only. It does not send commands and does not change the Energy-Aware algorithm.

## Safety / engine authority

- EMS authority remains `legacy_v0.6.4`.
- Entity Mapper remains `shadow_read_only`.
- Command Adapter remains locked / DRY_RUN.
- No real Zendure writes are enabled.
- No Energy-Aware discharge logic change.

This release prepares the next step: N-system (1–5 systems) engine generalization while preserving the v0.6.4 reference behavior.
