# Carpiquet EMS UI Kit

## Header Card

Must display:

- project name;
- motto;
- mode;
- engineering statement.

## Grid Card

Must display:

- live grid power;
- requested discharge;
- simulated grid result;
- target and deadband.

## Battery Card

Hyper and SolarFlow cards share the same structure:

- SOC gauge;
- PV power;
- simulated output;
- health state.

## EMS Card

Must display:

- Balance Index;
- minimum SOC;
- simulation state;
- grid-meter health.

## Health Card

Uses:

- binary health entities;
- explicit component names;
- overall score and status.

## History Card

Uses recorder-backed native Home Assistant history graphs.

## Accessibility

- text labels accompany icons;
- units are always visible;
- warning states are not indicated by colour alone;
- layouts remain usable on mobile screens.
