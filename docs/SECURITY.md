# Security Policy

## Safety Scope

Carpiquet EMS can influence energy-storage equipment. Every control feature must therefore fail safely.

## Supported Versions

Only the latest published alpha or beta version receives active fixes during development.

## Reporting

Do not publish sensitive Home Assistant configuration, credentials, MQTT passwords or private network addresses in public issues.

Security-sensitive reports should initially contain only:

- affected version;
- general description;
- reproducible impact;
- whether real control was enabled.

## Mandatory Safety Principles

- Simulation is the default.
- Real control must be explicitly enabled.
- Invalid or stale input data blocks commands.
- Minimum SOC and maximum power limits cannot be bypassed.
- Communication loss produces a safe state.
- No credential is stored in logs or diagnostics.
- Diagnostics must redact sensitive values.

## Golden Rule

> **Safety before performance. Always.**
