from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_GRID_DEADBAND,
    CONF_GRID_POWER_ENTITY,
    CONF_GRID_TARGET,
    CONF_HYPER_CAPACITY_KWH,
    CONF_HYPER_MAX_POWER_W,
    CONF_HYPER_OUTPUT_ENTITY,
    CONF_HYPER_PV_ENTITY,
    CONF_HYPER_SOC_ENTITY,
    CONF_MIN_SOC,
    CONF_SOLARFLOW_CAPACITY_KWH,
    CONF_SOLARFLOW_MAX_POWER_W,
    CONF_SOLARFLOW_OUTPUT_ENTITY,
    CONF_SOLARFLOW_PV_ENTITY,
    CONF_SOLARFLOW_SOC_ENTITY,
    DEFAULT_GRID_DEADBAND,
    DEFAULT_GRID_TARGET,
    DEFAULT_HYPER_CAPACITY_KWH,
    DEFAULT_HYPER_MAX_POWER_W,
    DEFAULT_MIN_SOC,
    DEFAULT_SOLARFLOW_CAPACITY_KWH,
    DEFAULT_SOLARFLOW_MAX_POWER_W,
    DOMAIN,
)


def _entity_selector(domain: str) -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=domain, multiple=False)
    )


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_GRID_POWER_ENTITY,
                default=defaults.get(CONF_GRID_POWER_ENTITY),
            ): _entity_selector("sensor"),
            vol.Required(
                CONF_HYPER_SOC_ENTITY,
                default=defaults.get(CONF_HYPER_SOC_ENTITY),
            ): _entity_selector("sensor"),
            vol.Required(
                CONF_HYPER_PV_ENTITY,
                default=defaults.get(CONF_HYPER_PV_ENTITY),
            ): _entity_selector("sensor"),
            vol.Required(
                CONF_HYPER_OUTPUT_ENTITY,
                default=defaults.get(CONF_HYPER_OUTPUT_ENTITY),
            ): _entity_selector("number"),
            vol.Required(
                CONF_SOLARFLOW_SOC_ENTITY,
                default=defaults.get(CONF_SOLARFLOW_SOC_ENTITY),
            ): _entity_selector("sensor"),
            vol.Required(
                CONF_SOLARFLOW_PV_ENTITY,
                default=defaults.get(CONF_SOLARFLOW_PV_ENTITY),
            ): _entity_selector("sensor"),
            vol.Required(
                CONF_SOLARFLOW_OUTPUT_ENTITY,
                default=defaults.get(CONF_SOLARFLOW_OUTPUT_ENTITY),
            ): _entity_selector("number"),
            vol.Required(
                CONF_HYPER_CAPACITY_KWH,
                default=defaults.get(
                    CONF_HYPER_CAPACITY_KWH, DEFAULT_HYPER_CAPACITY_KWH
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
            vol.Required(
                CONF_SOLARFLOW_CAPACITY_KWH,
                default=defaults.get(
                    CONF_SOLARFLOW_CAPACITY_KWH, DEFAULT_SOLARFLOW_CAPACITY_KWH
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
            vol.Required(
                CONF_HYPER_MAX_POWER_W,
                default=defaults.get(
                    CONF_HYPER_MAX_POWER_W, DEFAULT_HYPER_MAX_POWER_W
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=1, max=10000)),
            vol.Required(
                CONF_SOLARFLOW_MAX_POWER_W,
                default=defaults.get(
                    CONF_SOLARFLOW_MAX_POWER_W, DEFAULT_SOLARFLOW_MAX_POWER_W
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=1, max=10000)),
            vol.Required(
                CONF_MIN_SOC,
                default=defaults.get(CONF_MIN_SOC, DEFAULT_MIN_SOC),
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
            vol.Required(
                CONF_GRID_TARGET,
                default=defaults.get(CONF_GRID_TARGET, DEFAULT_GRID_TARGET),
            ): vol.All(vol.Coerce(float), vol.Range(min=-5000, max=5000)),
            vol.Required(
                CONF_GRID_DEADBAND,
                default=defaults.get(CONF_GRID_DEADBAND, DEFAULT_GRID_DEADBAND),
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=1000)),
        }
    )


DEFAULT_ENTITIES = {
    CONF_GRID_POWER_ENTITY: "sensor.shellypro3em_441d64748468_energy_meter_2_puissance",
    CONF_HYPER_SOC_ENTITY: "sensor.hyper_2000_electric_level",
    CONF_HYPER_PV_ENTITY: "sensor.hyper_2000_solar_input_power",
    CONF_HYPER_OUTPUT_ENTITY: "number.hyper_2000_output_limit",
    CONF_SOLARFLOW_SOC_ENTITY: "sensor.solarflow_2400_pro_electric_level",
    CONF_SOLARFLOW_PV_ENTITY: "sensor.solarflow_2400_pro_solar_input_power",
    CONF_SOLARFLOW_OUTPUT_ENTITY: "number.solarflow_2400_pro_output_limit",
}


class CarpiquetEMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Carpiquet EMS", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(DEFAULT_ENTITIES),
            description_placeholders={"mode": "SIMULATION"},
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CarpiquetEMSOptionsFlow:
        return CarpiquetEMSOptionsFlow(config_entry)


class CarpiquetEMSOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = dict(self._config_entry.data)
        defaults.update(self._config_entry.options)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults),
        )
