from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import *
from .topology import build_battery_entities, valid_numeric


BATTERY_TYPES = ["AB2000X", "AB3000L", "I2400"]

DEFAULT_ENTITIES = {
    CONF_GRID_POWER_ENTITY: "sensor.shellypro3em_441d64748468_energy_meter_2_puissance",
    CONF_HYPER_SOC_ENTITY: "sensor.hyper_2000_electric_level",
    CONF_HYPER_PV_ENTITY: "sensor.hyper_2000_solar_input_power",
    CONF_HYPER_OUTPUT_ENTITY: "number.hyper_2000_output_limit",
    CONF_SOLARFLOW_SOC_ENTITY: "sensor.solarflow_2400_pro_electric_level",
    CONF_SOLARFLOW_PV_ENTITY: "sensor.solarflow_2400_pro_solar_input_power",
    CONF_SOLARFLOW_OUTPUT_ENTITY: "number.solarflow_2400_pro_output_limit",
    CONF_HYPER_REAL_OUTPUT_ENTITY: "sensor.hyper_2000_output_home_power",
    CONF_SOLARFLOW_REAL_OUTPUT_ENTITY: "sensor.solarflow_2400_pro_output_home_power",
    CONF_HYPER_GRID_INPUT_ENTITY: DEFAULT_HYPER_GRID_INPUT_ENTITY,
    CONF_SOLARFLOW_GRID_INPUT_ENTITY: DEFAULT_SOLARFLOW_GRID_INPUT_ENTITY,
    CONF_HYPER_CAPACITY_ENTITY: "sensor.hyper_2000_total_kwh",
    CONF_SOLARFLOW_CAPACITY_ENTITY: "sensor.solarflow_2400_pro_total_kwh",
    CONF_HYPER_MAX_POWER_ENTITY: "sensor.hyper_2000_inverse_max_power",
    CONF_SOLARFLOW_MAX_POWER_ENTITY: "sensor.solarflow_2400_pro_inverse_max_power",
    CONF_HYPER_MIN_SOC_ENTITY: "number.hyper_2000_min_soc",
    CONF_HYPER_MAX_SOC_ENTITY: "number.hyper_2000_soc_set",
    CONF_SOLARFLOW_MIN_SOC_ENTITY: "number.solarflow_2400_pro_min_soc",
    CONF_SOLARFLOW_MAX_SOC_ENTITY: "number.solarflow_2400_pro_soc_set",
    CONF_GRID_TARGET: DEFAULT_GRID_TARGET,
    CONF_GRID_DEADBAND: DEFAULT_GRID_DEADBAND,
    CONF_RAMP_LIMIT_W: DEFAULT_RAMP_LIMIT_W,
    CONF_AUTOMATION_ENABLED: DEFAULT_AUTOMATION_ENABLED,
    CONF_AUTOMATION_MIN_HOLD_SECONDS: DEFAULT_AUTOMATION_MIN_HOLD_SECONDS,
    CONF_AUTOMATION_ALLOW_FALLBACK: DEFAULT_AUTOMATION_ALLOW_FALLBACK,
}

DYNAMIC_FALLBACKS = {
    CONF_HYPER_CAPACITY_ENTITY: (CONF_FALLBACK_HYPER_CAPACITY, 0.1, 100.0),
    CONF_SOLARFLOW_CAPACITY_ENTITY: (CONF_FALLBACK_SOLARFLOW_CAPACITY, 0.1, 100.0),
    CONF_HYPER_MAX_POWER_ENTITY: (CONF_FALLBACK_HYPER_MAX_POWER, 1.0, 10000.0),
    CONF_SOLARFLOW_MAX_POWER_ENTITY: (CONF_FALLBACK_SOLARFLOW_MAX_POWER, 1.0, 10000.0),
    CONF_HYPER_MIN_SOC_ENTITY: (CONF_FALLBACK_HYPER_MIN_SOC, 0.0, 100.0),
    CONF_HYPER_MAX_SOC_ENTITY: (CONF_FALLBACK_HYPER_MAX_SOC, 0.0, 100.0),
    CONF_SOLARFLOW_MIN_SOC_ENTITY: (CONF_FALLBACK_SOLARFLOW_MIN_SOC, 0.0, 100.0),
    CONF_SOLARFLOW_MAX_SOC_ENTITY: (CONF_FALLBACK_SOLARFLOW_MAX_SOC, 0.0, 100.0),
}


def _entity(domain: str):
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=domain, multiple=False)
    )


def _battery_type_selector():
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=BATTERY_TYPES,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _text_selector():
    return selector.TextSelector(
        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
    )


MAIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GRID_POWER_ENTITY): _entity("sensor"),
        vol.Required(CONF_HYPER_SOC_ENTITY): _entity("sensor"),
        vol.Required(CONF_HYPER_PV_ENTITY): _entity("sensor"),
        vol.Required(CONF_HYPER_OUTPUT_ENTITY): _entity("number"),
        vol.Required(CONF_SOLARFLOW_SOC_ENTITY): _entity("sensor"),
        vol.Required(CONF_SOLARFLOW_PV_ENTITY): _entity("sensor"),
        vol.Required(CONF_SOLARFLOW_OUTPUT_ENTITY): _entity("number"),
        vol.Required(CONF_HYPER_REAL_OUTPUT_ENTITY): _entity("sensor"),
        vol.Required(CONF_SOLARFLOW_REAL_OUTPUT_ENTITY): _entity("sensor"),
        vol.Required(CONF_HYPER_GRID_INPUT_ENTITY): _entity("sensor"),
        vol.Required(CONF_SOLARFLOW_GRID_INPUT_ENTITY): _entity("sensor"),
        vol.Required(CONF_HYPER_CAPACITY_ENTITY): _entity("sensor"),
        vol.Required(CONF_SOLARFLOW_CAPACITY_ENTITY): _entity("sensor"),
        vol.Required(CONF_HYPER_MAX_POWER_ENTITY): _entity("sensor"),
        vol.Required(CONF_SOLARFLOW_MAX_POWER_ENTITY): _entity("sensor"),
        vol.Required(CONF_HYPER_MIN_SOC_ENTITY): _entity("number"),
        vol.Required(CONF_HYPER_MAX_SOC_ENTITY): _entity("number"),
        vol.Required(CONF_SOLARFLOW_MIN_SOC_ENTITY): _entity("number"),
        vol.Required(CONF_SOLARFLOW_MAX_SOC_ENTITY): _entity("number"),
        vol.Required(CONF_GRID_TARGET): vol.All(
            vol.Coerce(float), vol.Range(min=-5000, max=5000)
        ),
        vol.Required(CONF_GRID_DEADBAND): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=1000)
        ),
        vol.Required(CONF_RAMP_LIMIT_W): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=5000)
        ),
        vol.Required(CONF_AUTOMATION_ENABLED): bool,
        vol.Required(CONF_AUTOMATION_MIN_HOLD_SECONDS): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=300)
        ),
        vol.Required(CONF_AUTOMATION_ALLOW_FALLBACK): bool,
    }
)


def _schema_with_values(flow, schema: vol.Schema, values: dict[str, Any]) -> vol.Schema:
    """Apply suggested values without changing which keys the schema accepts."""
    return flow.add_suggested_values_to_schema(schema, values)


def _read_float(hass, entity_id: str):
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable", "", None):
        return None
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None


def _pack_count(hass, entity_id: str) -> int:
    value = _read_float(hass, entity_id)
    if value is None:
        return 0
    return max(0, min(16, int(value)))


def _battery_schema(hyper_count: int, solar_count: int) -> vol.Schema:
    schema: dict[Any, Any] = {}
    for system, count in (("hyper", hyper_count), ("solarflow", solar_count)):
        for index in range(1, count + 1):
            schema[vol.Required(f"{system}_battery_{index}_type")] = _battery_type_selector()
            schema[vol.Required(f"{system}_battery_{index}_serial")] = _text_selector()
    return vol.Schema(schema)


def _battery_defaults(batteries: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    counters = {"hyper": 0, "solarflow": 0}
    for battery in batteries:
        system = battery[CONF_BATTERY_SYSTEM]
        counters[system] += 1
        index = counters[system]
        result[f"{system}_battery_{index}_type"] = battery[CONF_BATTERY_TYPE]
        result[f"{system}_battery_{index}_serial"] = battery[CONF_BATTERY_SERIAL]
    return result


def _validate_serials(user_input, hyper_count: int, solar_count: int) -> bool:
    for system, count in (("hyper", hyper_count), ("solarflow", solar_count)):
        for index in range(1, count + 1):
            serial = str(user_input.get(f"{system}_battery_{index}_serial", "")).strip()
            if not re.fullmatch(r"\d{5}", serial):
                return False
    return True


def _build_batteries(hass, user_input, hyper_count, solar_count):
    batteries = []
    for system, count in (("hyper", hyper_count), ("solarflow", solar_count)):
        for index in range(1, count + 1):
            battery_type = str(
                user_input[f"{system}_battery_{index}_type"]
            ).strip().upper()
            serial = str(
                user_input[f"{system}_battery_{index}_serial"]
            ).strip()

            if battery_type not in BATTERY_TYPES:
                return [], {"base": "battery_type_invalid"}

            entities = build_battery_entities(battery_type, serial)
            required = ("soc_level", "power", "state")
            if any(hass.states.get(entities[key]) is None for key in required):
                return [], {"base": "battery_not_found"}

            batteries.append(
                {
                    CONF_BATTERY_SYSTEM: system,
                    CONF_BATTERY_TYPE: battery_type,
                    CONF_BATTERY_SERIAL: serial,
                    CONF_BATTERY_ENTITIES: entities,
                }
            )
    return batteries, {}


def _seed_fallbacks(hass, data):
    errors = {}
    for entity_key, (fallback_key, minimum, maximum) in DYNAMIC_FALLBACKS.items():
        value = _read_float(hass, data[entity_key])
        if value is None or not valid_numeric(value, minimum, maximum):
            errors["base"] = "dynamic_value_unavailable"
            continue
        data[fallback_key] = float(value)
    return errors


class CarpiquetEMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    def __init__(self):
        self._pending: dict[str, Any] = {}
        self._hyper_count = 0
        self._solar_count = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        values = DEFAULT_ENTITIES if user_input is None else user_input

        if user_input is not None:
            data = dict(user_input)
            errors = _seed_fallbacks(self.hass, data)

            self._hyper_count = _pack_count(self.hass, HYPER_PACK_NUM_ENTITY)
            self._solar_count = _pack_count(self.hass, SOLARFLOW_PACK_NUM_ENTITY)

            if self._hyper_count < 1 or self._solar_count < 1:
                errors["base"] = "pack_count_unavailable"

            if not errors:
                self._pending = data
                return await self.async_step_batteries()

        return self.async_show_form(
            step_id="user",
            data_schema=_schema_with_values(self, MAIN_SCHEMA, values),
            errors=errors,
            description_placeholders={"mode": "SIMULATION"},
        )

    async def async_step_batteries(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        schema = _battery_schema(self._hyper_count, self._solar_count)
        errors: dict[str, str] = {}
        values: dict[str, Any] = {}

        if user_input is not None:
            values = user_input
            if not _validate_serials(
                user_input, self._hyper_count, self._solar_count
            ):
                errors["base"] = "serial_must_be_five_digits"
            else:
                batteries, errors = _build_batteries(
                    self.hass,
                    user_input,
                    self._hyper_count,
                    self._solar_count,
                )
                if not errors:
                    self._pending[CONF_BATTERIES] = batteries
                    return self.async_create_entry(
                        title="Carpiquet EMS",
                        data=self._pending,
                    )

        return self.async_show_form(
            step_id="batteries",
            data_schema=_schema_with_values(self, schema, values),
            errors=errors,
            description_placeholders={
                "hyper_count": str(self._hyper_count),
                "solarflow_count": str(self._solar_count),
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return CarpiquetEMSOptionsFlow(config_entry)


class CarpiquetEMSOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry
        self._pending: dict[str, Any] = {}
        self._hyper_count = 0
        self._solar_count = 0

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        defaults = dict(self._config_entry.data)
        defaults.update(self._config_entry.options)

        errors: dict[str, str] = {}
        values = defaults if user_input is None else user_input

        if user_input is not None:
            self._pending = dict(user_input)
            self._hyper_count = _pack_count(self.hass, HYPER_PACK_NUM_ENTITY)
            self._solar_count = _pack_count(self.hass, SOLARFLOW_PACK_NUM_ENTITY)

            if self._hyper_count < 1 or self._solar_count < 1:
                errors["base"] = "pack_count_unavailable"

            if not errors:
                return await self.async_step_batteries()

        return self.async_show_form(
            step_id="init",
            data_schema=_schema_with_values(self, MAIN_SCHEMA, values),
            errors=errors,
        )

    async def async_step_batteries(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        schema = _battery_schema(self._hyper_count, self._solar_count)
        existing = self._config_entry.data.get(CONF_BATTERIES, [])
        values = (
            _battery_defaults(existing)
            if user_input is None
            else user_input
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            if not _validate_serials(
                user_input, self._hyper_count, self._solar_count
            ):
                errors["base"] = "serial_must_be_five_digits"
            else:
                batteries, errors = _build_batteries(
                    self.hass,
                    user_input,
                    self._hyper_count,
                    self._solar_count,
                )
                if not errors:
                    self._pending[CONF_BATTERIES] = batteries
                    return self.async_create_entry(
                        title="",
                        data=self._pending,
                    )

        return self.async_show_form(
            step_id="batteries",
            data_schema=_schema_with_values(self, schema, values),
            errors=errors,
        )
