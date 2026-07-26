# RFC-0004 — EMS Core Logic

## Status
Accepted — Sprint 5 revision v0.4.1.

## Dynamic Zendure values
Eight installation values are selected as Home Assistant entities:
- Hyper / SolarFlow total capacity
- Hyper / SolarFlow maximum AC power
- Hyper / SolarFlow minimum SOC
- Hyper / SolarFlow maximum SOC

At installation, the current valid values seed persistent fallbacks.

At runtime:
1. valid live Zendure value → used immediately;
2. if different from stored fallback → fallback is updated;
3. unavailable / invalid live value → last valid fallback is used;
4. `Data Mode` reports `LIVE` or `FALLBACK ACTIF`.

## Battery topology
`pack_num` determines how many batteries must be identified.
The user enters only battery type + serial number.
Carpiquet EMS derives and validates the BMS entity IDs.

## Safety
Simulation only. No Zendure output-limit write is enabled.
