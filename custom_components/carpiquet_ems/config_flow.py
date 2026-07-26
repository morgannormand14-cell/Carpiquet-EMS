from __future__ import annotations

from typing import Any

import re
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import *
from .topology import build_battery_entities, valid_numeric

DEFAULT_ENTITIES = {
    CONF_GRID_POWER_ENTITY: "sensor.shellypro3em_441d64748468_energy_meter_2_puissance",
    CONF_HYPER_SOC_ENTITY: "sensor.hyper_2000_electric_level",
    CONF_HYPER_PV_ENTITY: "sensor.hyper_2000_solar_input_power",
    CONF_HYPER_OUTPUT_ENTITY: "number.hyper_2000_output_limit",
    CONF_SOLARFLOW_SOC_ENTITY: "sensor.solarflow_2400_pro_electric_level",
    CONF_SOLARFLOW_PV_ENTITY: "sensor.solarflow_2400_pro_solar_input_power",
    CONF_SOLARFLOW_OUTPUT_ENTITY: "number.solarflow_2400_pro_output_limit",
    CONF_HYPER_CAPACITY_ENTITY: "sensor.hyper_2000_total_kwh",
    CONF_SOLARFLOW_CAPACITY_ENTITY: "sensor.solarflow_2400_pro_total_kwh",
    CONF_HYPER_MAX_POWER_ENTITY: "sensor.hyper_2000_inverse_max_power",
    CONF_SOLARFLOW_MAX_POWER_ENTITY: "sensor.solarflow_2400_pro_inverse_max_power",
    CONF_HYPER_MIN_SOC_ENTITY: "number.hyper_2000_min_soc",
    CONF_HYPER_MAX_SOC_ENTITY: "number.hyper_2000_soc_set",
    CONF_SOLARFLOW_MIN_SOC_ENTITY: "number.solarflow_2400_pro_min_soc",
    CONF_SOLARFLOW_MAX_SOC_ENTITY: "number.solarflow_2400_pro_soc_set",
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
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain, multiple=False))

def _text():
    return selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT))

def _battery_type_selector():
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=["AB2000X", "AB3000L", "I2400"],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )

def _serial_validator(value: str) -> str:
    serial = str(value).strip()
    if not re.fullmatch(r"\d{5}", serial):
        raise vol.Invalid("serial_must_be_five_digits")
    return serial

def _main_schema(defaults: dict[str, Any]) -> vol.Schema:
    fields = {
        CONF_GRID_POWER_ENTITY: "sensor",
        CONF_HYPER_SOC_ENTITY: "sensor",
        CONF_HYPER_PV_ENTITY: "sensor",
        CONF_HYPER_OUTPUT_ENTITY: "number",
        CONF_SOLARFLOW_SOC_ENTITY: "sensor",
        CONF_SOLARFLOW_PV_ENTITY: "sensor",
        CONF_SOLARFLOW_OUTPUT_ENTITY: "number",
        CONF_HYPER_CAPACITY_ENTITY: "sensor",
        CONF_SOLARFLOW_CAPACITY_ENTITY: "sensor",
        CONF_HYPER_MAX_POWER_ENTITY: "sensor",
        CONF_SOLARFLOW_MAX_POWER_ENTITY: "sensor",
        CONF_HYPER_MIN_SOC_ENTITY: "number",
        CONF_HYPER_MAX_SOC_ENTITY: "number",
        CONF_SOLARFLOW_MIN_SOC_ENTITY: "number",
        CONF_SOLARFLOW_MAX_SOC_ENTITY: "number",
    }
    schema = {}
    for key, domain in fields.items():
        schema[vol.Required(key, default=defaults.get(key, DEFAULT_ENTITIES.get(key)))] = _entity(domain)
    schema[vol.Required(CONF_GRID_TARGET, default=defaults.get(CONF_GRID_TARGET, DEFAULT_GRID_TARGET))] = vol.All(vol.Coerce(float), vol.Range(min=-5000, max=5000))
    schema[vol.Required(CONF_GRID_DEADBAND, default=defaults.get(CONF_GRID_DEADBAND, DEFAULT_GRID_DEADBAND))] = vol.All(vol.Coerce(float), vol.Range(min=0, max=1000))
    schema[vol.Required(CONF_RAMP_LIMIT_W, default=defaults.get(CONF_RAMP_LIMIT_W, DEFAULT_RAMP_LIMIT_W))] = vol.All(vol.Coerce(float), vol.Range(min=0, max=5000))
    return vol.Schema(schema)

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

def _battery_schema(hyper_count: int, solar_count: int, defaults: dict[str, Any] | None = None):
    defaults = defaults or {}
    schema = {}
    for system, count in (("hyper", hyper_count), ("solarflow", solar_count)):
        for index in range(1, count + 1):
            type_key = f"{system}_battery_{index}_type"
            serial_key = f"{system}_battery_{index}_serial"
            schema[vol.Required(type_key, default=defaults.get(type_key, "AB2000X"))] = _battery_type_selector()
            schema[vol.Required(serial_key, default=defaults.get(serial_key, ""))] = vol.All(_text(), _serial_validator)
    return vol.Schema(schema)

def _battery_defaults(batteries: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    counters = {"hyper": 0, "solarflow": 0}
    for battery in batteries:
        system = battery[CONF_BATTERY_SYSTEM]
        counters[system] += 1
        i = counters[system]
        out[f"{system}_battery_{i}_type"] = battery[CONF_BATTERY_TYPE]
        out[f"{system}_battery_{i}_serial"] = battery[CONF_BATTERY_SERIAL]
    return out

def _build_batteries(hass, user_input, hyper_count, solar_count):
    batteries = []
    errors = {}
    for system, count in (("hyper", hyper_count), ("solarflow", solar_count)):
        for index in range(1, count + 1):
            t = str(user_input[f"{system}_battery_{index}_type"]).strip()
            serial = str(user_input[f"{system}_battery_{index}_serial"]).strip()
            entities = build_battery_entities(t, serial)
            # Validate the three core BMS entities before accepting the battery.
            required = ("soc_level", "power", "state")
            if not t or not serial or any(hass.states.get(entities[k]) is None for k in required):
                errors["base"] = "battery_not_found"
                continue
            batteries.append({
                CONF_BATTERY_SYSTEM: system,
                CONF_BATTERY_TYPE: t.upper(),
                CONF_BATTERY_SERIAL: serial,
                CONF_BATTERY_ENTITIES: entities,
            })
    return batteries, errors

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
    VERSION = 2

    def __init__(self):
        self._pending = {}
        self._hyper_count = 0
        self._solar_count = 0

    async def async_step_user(self, user_input=None) -> FlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

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

            return self.async_show_form(step_id="user", data_schema=_main_schema(data), errors=errors)

        return self.async_show_form(
            step_id="user",
            data_schema=_main_schema(DEFAULT_ENTITIES),
            description_placeholders={"mode": "SIMULATION"},
        )

    async def async_step_batteries(self, user_input=None) -> FlowResult:
        if user_input is not None:
            batteries, errors = _build_batteries(
                self.hass, user_input, self._hyper_count, self._solar_count
            )
            if not errors:
                self._pending[CONF_BATTERIES] = batteries
                return self.async_create_entry(title="Carpiquet EMS", data=self._pending)
            return self.async_show_form(
                step_id="batteries",
                data_schema=_battery_schema(self._hyper_count, self._solar_count, user_input),
                errors=errors,
                description_placeholders={
                    "hyper_count": str(self._hyper_count),
                    "solarflow_count": str(self._solar_count),
                },
            )

        return self.async_show_form(
            step_id="batteries",
            data_schema=_battery_schema(self._hyper_count, self._solar_count),
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
        self._pending = {}
        self._hyper_count = 0
        self._solar_count = 0

    async def async_step_init(self, user_input=None) -> FlowResult:
        defaults = dict(self._config_entry.data)
        defaults.update(self._config_entry.options)

        if user_input is not None:
            self._pending = dict(user_input)
            self._hyper_count = _pack_count(self.hass, HYPER_PACK_NUM_ENTITY)
            self._solar_count = _pack_count(self.hass, SOLARFLOW_PACK_NUM_ENTITY)
            errors = {}
            if self._hyper_count < 1 or self._solar_count < 1:
                errors["base"] = "pack_count_unavailable"
            if not errors:
                return await self.async_step_batteries()
            return self.async_show_form(step_id="init", data_schema=_main_schema(user_input), errors=errors)

        return self.async_show_form(step_id="init", data_schema=_main_schema(defaults))

    async def async_step_batteries(self, user_input=None) -> FlowResult:
        existing = self._config_entry.data.get(CONF_BATTERIES, [])
        defaults = _battery_defaults(existing)
        if user_input is not None:
            batteries, errors = _build_batteries(
                self.hass, user_input, self._hyper_count, self._solar_count
            )
            if not errors:
                self._pending[CONF_BATTERIES] = batteries
                return self.async_create_entry(title="", data=self._pending)
            defaults = user_input
            return self.async_show_form(
                step_id="batteries",
                data_schema=_battery_schema(self._hyper_count, self._solar_count, defaults),
                errors=errors,
            )

        return self.async_show_form(
            step_id="batteries",
            data_schema=_battery_schema(self._hyper_count, self._solar_count, defaults),
        )
