# 🏴 Carpiquet EMS --- EMS Specification

> **Every watt counts.**
>
> **Intelligent energy management for Zendure.**
>
> *Designed with ❤️ in Normandy.*

------------------------------------------------------------------------

# 1. Purpose

This document defines the functional specification of the Carpiquet EMS.

It describes what the EMS must do independently of the implementation.

Every algorithm, test and future feature shall comply with this
specification.

------------------------------------------------------------------------

# 2. Scope

Current supported platform:

-   Home Assistant
-   Zendure Hyper 2000
-   Zendure SolarFlow 2400 Pro
-   Shelly Pro 3EM
-   MQTT

Future:

-   Additional Zendure devices
-   Multiple battery systems
-   Forecast providers
-   Dynamic tariffs

------------------------------------------------------------------------

# 3. Definitions

  Term              Definition
  ----------------- -----------------------------------
  SOC               Battery State of Charge (%)
  Grid Target       Desired grid power (default: 0 W)
  Deadband          No-action zone around Grid Target
  PV                Photovoltaic production
  Decision Engine   Calculates power allocation
  Safety Engine     Ensures safe operation
  Balance Index     Indicator of battery balance
  Health Score      Overall system health

------------------------------------------------------------------------

# 4. Functional Rules

## EMS-001 --- Grid Target

Maintain the measured grid power as close as possible to the configured
Grid Target.

Priority: High

## EMS-002 --- Deadband

No correction while:

    |Grid Power - Target| < Deadband

Default: 20 W

Priority: High

## EMS-003 --- Minimum SOC Protection

No battery shall discharge below the configured minimum SOC.

Priority: Critical

## EMS-004 --- Maximum Output

Never exceed the maximum power of each inverter.

Priority: Critical

## EMS-005 --- PV Priority

Always consider PV production before requesting battery discharge.

Priority: High

## EMS-006 --- Power Allocation

Distribute requested power across available battery systems.

Priority: High

## EMS-007 --- Battery Energy Balancing

Allocate discharge so all batteries converge toward the minimum SOC at
approximately the same time.

Priority: Critical

## EMS-008 --- Zero Export Strategy

When enabled, minimise grid export while respecting all safety limits.

## EMS-009 --- Zero Import Strategy

When enabled, minimise grid import whenever battery energy is available.

## EMS-010 --- Fail Safe

If system integrity cannot be guaranteed, stop issuing power commands.

Priority: Critical

------------------------------------------------------------------------

# 5. Safety Rules

The Safety Engine always has priority.

Mandatory protections:

-   Minimum SOC
-   Maximum output
-   Invalid sensor values
-   Communication timeout
-   Emergency stop
-   Configuration validation

------------------------------------------------------------------------

# 6. Battery Management

Monitor continuously:

-   SOC
-   Remaining energy
-   Maximum discharge power
-   Available PV
-   Battery availability

------------------------------------------------------------------------

# 7. Grid Management

Monitor:

-   Import
-   Export
-   Grid Target
-   Deadband
-   Grid correction

------------------------------------------------------------------------

# 8. Simulation Mode

Simulation is the default operating mode.

Requirements:

-   No command sent to Zendure devices.
-   Full calculation pipeline active.
-   Complete diagnostics available.

------------------------------------------------------------------------

# 9. Diagnostics

Monitor:

-   Home Assistant
-   Shelly Pro 3EM
-   Zendure HA
-   MQTT
-   Hyper 2000
-   SolarFlow 2400 Pro

Outputs:

-   Health Score
-   Errors
-   Warnings

------------------------------------------------------------------------

# 10. Future Extensions

-   Weather forecast
-   PV prediction
-   Dynamic tariffs
-   AI-assisted optimisation
-   Multi-battery support

------------------------------------------------------------------------

# Compliance

Each implementation shall reference the corresponding EMS rule.

Each functional rule shall have automated tests.

------------------------------------------------------------------------

© Carpiquet EMS Project
