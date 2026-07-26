# 🏴 Carpiquet EMS

> **Every watt counts.**
>
> **Intelligent energy management for Zendure.**
>
> *Designed with ❤️ in Normandy.*

# 🤖 Sprint 5 — Automation Engine

Carpiquet EMS gains a deterministic automation state machine between the EMS Core and the future actuator layer.

## States
- ✅ Disabled
- ✅ Safe Hold
- ✅ Idle
- ✅ Discharge

## Safety
- ✅ Grid-meter availability gate
- ✅ Battery availability gate
- ✅ Fallback policy gate
- ✅ Minimum state hold to reduce oscillation
- ✅ Immediate safety-state transitions
- ✅ Simulation Mode permanently enforced

## Dashboard
- ✅ New Automation view
- ✅ State and reason
- ✅ Safety gate
- ✅ Automation request
- ✅ Cycle counter
- ✅ Last transition
- ✅ Hold timer
- ✅ 24 h decision history

## Critical boundary
**100% simulation-only.**

No real command is sent to:
- `number.hyper_2000_output_limit`
- `number.solarflow_2400_pro_output_limit`

Tag: `v0.5.0-alpha-sprint5`
Pre-release: **Yes**

🏴 **Carpiquet EMS — Every watt counts.**
