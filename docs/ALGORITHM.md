# 🏴 Carpiquet EMS Algorithm Reference

## Status

This document describes the current simulation baseline and the target direction. It is not yet the final intelligent balancing algorithm.

## Grid Error

```text
grid_error = measured_grid_power - grid_target
```

Positive values represent import. Negative values represent export.

## Deadband

No discharge correction is requested when:

```text
grid_error <= deadband
```

For the current import-reduction strategy:

```text
requested_discharge = max(0, grid_error)
```

outside the deadband.

## Usable Battery Energy

```text
usable_energy_kwh =
    max(0, SOC - minimum_SOC)
    × capacity_kwh
    ÷ 100
```

A battery at or below minimum SOC has zero usable discharge energy.

## Current Allocation Baseline

Requested discharge is distributed in proportion to usable energy, then constrained by each inverter maximum.

## Target Balancing Algorithm

The future algorithm must minimise the difference between predicted times to minimum SOC:

```text
time_to_minimum_hyper ≈ time_to_minimum_solarflow
```

while respecting:

- inverter power limits;
- minimum SOC;
- available PV;
- stale or invalid data;
- configured grid target;
- anti-oscillation limits.

## Balance Index

The current Balance Index is a simple SOC-difference indicator. It is diagnostic only and will be revised before real control.
