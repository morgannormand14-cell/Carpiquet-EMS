# 🏴 Carpiquet EMS Architecture

## Purpose

This document describes the intended software architecture independently of implementation details.

## High-Level Data Flow

```text
Home Assistant entity states
          │
          ▼
Acquisition Layer
          │
          ├── Shelly Pro 3EM
          ├── Zendure Hyper 2000
          └── Zendure SolarFlow 2400 Pro
          │
          ▼
Validation and Safety Layer
          │
          ▼
Decision Engine
          │
          ├── Grid strategy
          ├── Battery balancing
          └── Power allocation
          │
          ▼
Simulation Output / Command Gateway
          │
          ▼
Home Assistant entities and diagnostics
```

## Layers

### Presentation Layer
Dashboard, configuration, diagnostics, documentation and health status.

### Home Assistant Integration Layer
Config flow, coordinator, entities, services and diagnostics.

### Core Layer
Pure calculations: safety, balancing, allocation, scheduling and statistics.

### Device Adapter Layer
Normalises device-specific Home Assistant entities into common EMS models.

## Architectural Rules

- The Safety Engine has priority over all optimisation.
- Core calculations must not depend directly on Home Assistant APIs.
- Simulation and real control use the same decision pipeline.
- Real commands pass through a dedicated command gateway.
- Every critical behaviour must map to an EMS specification rule.
- Device-specific details remain in adapters.

## Current Target Devices

- Shelly Pro 3EM
- Zendure Hyper 2000
- Zendure SolarFlow 2400 Pro

## Future Extensibility

Adding a device should require a new adapter, not a rewrite of the Decision Engine.
