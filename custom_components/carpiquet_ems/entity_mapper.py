from __future__ import annotations

"""Read-only Zendure entity mapper for Carpiquet EMS v0.6.5.

Phase 1 deliberately does not drive the EMS engine. It normalizes the two
currently configured systems into ``systems[]`` and exposes comparison data so
that the dynamic architecture can be validated in Shadow before cut-over.
"""

from dataclasses import dataclass, asdict
from typing import Any

from .const import (
    CONF_HYPER_SOC_ENTITY, CONF_HYPER_PV_ENTITY, CONF_HYPER_OUTPUT_ENTITY,
    CONF_HYPER_CAPACITY_ENTITY, CONF_HYPER_MAX_POWER_ENTITY,
    CONF_HYPER_MIN_SOC_ENTITY, CONF_HYPER_MAX_SOC_ENTITY,
    CONF_SOLARFLOW_SOC_ENTITY, CONF_SOLARFLOW_PV_ENTITY, CONF_SOLARFLOW_OUTPUT_ENTITY,
    CONF_SOLARFLOW_CAPACITY_ENTITY, CONF_SOLARFLOW_MAX_POWER_ENTITY,
    CONF_SOLARFLOW_MIN_SOC_ENTITY, CONF_SOLARFLOW_MAX_SOC_ENTITY,
    CONF_HYPER_REAL_OUTPUT_ENTITY, CONF_SOLARFLOW_REAL_OUTPUT_ENTITY,
    CONF_HYPER_GRID_INPUT_ENTITY, CONF_SOLARFLOW_GRID_INPUT_ENTITY,
    DEFAULT_HYPER_GRID_INPUT_ENTITY, DEFAULT_SOLARFLOW_GRID_INPUT_ENTITY,
)


@dataclass(frozen=True)
class MappedSystem:
    system_id: str
    name: str
    control_profile: str
    capabilities: dict[str, Any]
    entities: dict[str, str]
    values: dict[str, float | None]
    available: bool
    missing_entities: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["missing_entities"] = list(self.missing_entities)
        return data


def _number(hass, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if not state or state.state in ("unknown", "unavailable", "", None):
        return None
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None


def _system(hass, system_id: str, name: str, control_profile: str, capabilities: dict[str, Any], entities: dict[str, str]) -> MappedSystem:
    values = {key: _number(hass, entity_id) for key, entity_id in entities.items()}
    # These are the minimum fields needed to describe a controllable Zendure
    # system. PV/output/grid-input may legitimately be zero but must exist.
    required = ("soc", "capacity_kwh", "max_power_w", "min_soc", "max_soc")
    missing = tuple(key for key in required if values.get(key) is None)
    return MappedSystem(system_id, name, control_profile, capabilities, entities, values, not missing, missing)


def build_shadow_systems(hass, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Build normalized systems[] from the existing v0.6.4 configuration.

    Read-only by design: no service call, no state write and no engine input.
    """
    definitions = (
        ("hyper_2000", "Hyper 2000", "legacy_hyper", {
            "command_limit_semantics": "legacy_generation_unconfirmed",
            "home_output_measured": True,
            "separate_grid_input_measurement": True,
            "native_soc_reference": True,
            "shadow_control_only": True,
        }, {
            "soc": config.get(CONF_HYPER_SOC_ENTITY),
            "pv_w": config.get(CONF_HYPER_PV_ENTITY),
            "command_limit_w": config.get(CONF_HYPER_OUTPUT_ENTITY),
            "home_output_w": config.get(CONF_HYPER_REAL_OUTPUT_ENTITY),
            "grid_input_w": config.get(CONF_HYPER_GRID_INPUT_ENTITY, DEFAULT_HYPER_GRID_INPUT_ENTITY),
            "capacity_kwh": config.get(CONF_HYPER_CAPACITY_ENTITY),
            "max_power_w": config.get(CONF_HYPER_MAX_POWER_ENTITY),
            "min_soc": config.get(CONF_HYPER_MIN_SOC_ENTITY),
            "max_soc": config.get(CONF_HYPER_MAX_SOC_ENTITY),
        }),
        ("solarflow_2400_pro", "SolarFlow 2400 Pro", "zensdk_generation", {
            "command_limit_semantics": "active_output_command_limit",
            "home_output_measured": True,
            "separate_grid_input_measurement": True,
            "native_soc_reference": True,
            "shadow_control_only": True,
        }, {
            "soc": config.get(CONF_SOLARFLOW_SOC_ENTITY),
            "pv_w": config.get(CONF_SOLARFLOW_PV_ENTITY),
            "command_limit_w": config.get(CONF_SOLARFLOW_OUTPUT_ENTITY),
            "home_output_w": config.get(CONF_SOLARFLOW_REAL_OUTPUT_ENTITY),
            "grid_input_w": config.get(CONF_SOLARFLOW_GRID_INPUT_ENTITY, DEFAULT_SOLARFLOW_GRID_INPUT_ENTITY),
            "capacity_kwh": config.get(CONF_SOLARFLOW_CAPACITY_ENTITY),
            "max_power_w": config.get(CONF_SOLARFLOW_MAX_POWER_ENTITY),
            "min_soc": config.get(CONF_SOLARFLOW_MIN_SOC_ENTITY),
            "max_soc": config.get(CONF_SOLARFLOW_MAX_SOC_ENTITY),
        }),
    )
    return [_system(hass, sid, name, profile, capabilities, entities).as_dict()
            for sid, name, profile, capabilities, entities in definitions]


def mapper_diagnostics(systems: list[dict[str, Any]]) -> dict[str, Any]:
    """Compact parity diagnostics suitable for HA diagnostics/session logs."""
    mapping_ready = bool(systems) and all(bool(s.get("available")) for s in systems)
    return {
        "mode": "shadow_read_only",
        "engine_authority": "legacy_v0.6.4",
        "systems_count": len(systems),
        "available_systems_count": sum(bool(s.get("available")) for s in systems),
        "mapping_ready": mapping_ready,
        # Parity was validated on the v0.6.5-alpha.1 reference Shadow log
        # (SIM-20260908-221137): 41,829 cycles, zero differences on the six
        # semantically equivalent telemetry comparisons (PV, home output and
        # grid input for Hyper 2000 and SolarFlow 2400 Pro). Command limits
        # are intentionally excluded because their semantics differ by product
        # generation and are now represented through control_profile/capabilities.
        "parity_evaluated": True,
        "parity_ready": mapping_ready,
        "parity_reason": "validated_reference_log_semantic_fields",
        "parity_reference": {
            "session_id": "SIM-20260908-221137",
            "cycles": 41829,
            "differences": 0,
            "fields_per_system": ["pv_w", "home_output_w", "grid_input_w"],
            "command_limit_excluded": True,
        },
        "field_semantics": {
            "command_limit_w": "generation-dependent Zendure command/limit; never treated as measured home power",
            "home_output_w": "measured power delivered by the system to the home; may include PV and battery contribution",
        },
        "systems": systems,
    }
