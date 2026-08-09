# Carpiquet EMS v0.6.0-alpha-sprint6 — Command Pipeline & Shadow Mode

> **Every watt counts.**  
> Intelligent energy management for Zendure.  
> Designed with ❤️ in Normandy.  
> Engineered for reliability. Built for Home Assistant.

Sprint 6 introduces the command-control architecture that will eventually sit
between the Carpiquet EMS energy engine and Zendure devices.

## New: Command Pipeline

The digital twin now produces a requested command. A separate safety controller
validates, limits or rejects that request before it reaches the future command adapter.

## New: Shadow Mode

Shadow Mode records requested and validated output commands, current Zendure
output-limit settings, command deltas, safety status and the command that would
have been sent.

## Control modes

- Simulation
- Shadow
- Armed

**Armed does not enable writes in v0.6.0.**

Every Home Assistant reload automatically returns the mode to **Simulation**.

## Safety

The v0.6.0 package contains no real Zendure command path.

> **Safety before performance. Always.**

Tag: `v0.6.0-alpha-sprint6`
Pre-release: **Yes**
