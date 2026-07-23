import voluptuous as vol
from homeassistant import config_entries
from .const import *

class CarpiquetEMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Carpiquet EMS", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_GRID_POWER_ENTITY, default="sensor.shellypro3em_441d64748468_energy_meter_2_puissance"): str,
            vol.Required(CONF_HYPER_SOC_ENTITY, default="sensor.hyper_2000_electric_level"): str,
            vol.Required(CONF_HYPER_PV_ENTITY, default="sensor.hyper_2000_solar_input_power"): str,
            vol.Required(CONF_HYPER_OUTPUT_ENTITY, default="number.hyper_2000_output_limit"): str,
            vol.Required(CONF_SOLARFLOW_SOC_ENTITY, default="sensor.solarflow_2400_pro_electric_level"): str,
            vol.Required(CONF_SOLARFLOW_PV_ENTITY, default="sensor.solarflow_2400_pro_solar_input_power"): str,
            vol.Required(CONF_SOLARFLOW_OUTPUT_ENTITY, default="number.solarflow_2400_pro_output_limit"): str,
            vol.Required(CONF_HYPER_CAPACITY_KWH, default=DEFAULT_HYPER_CAPACITY_KWH): vol.Coerce(float),
            vol.Required(CONF_SOLARFLOW_CAPACITY_KWH, default=DEFAULT_SOLARFLOW_CAPACITY_KWH): vol.Coerce(float),
            vol.Required(CONF_HYPER_MAX_POWER_W, default=DEFAULT_HYPER_MAX_POWER_W): vol.Coerce(float),
            vol.Required(CONF_SOLARFLOW_MAX_POWER_W, default=DEFAULT_SOLARFLOW_MAX_POWER_W): vol.Coerce(float),
            vol.Required(CONF_MIN_SOC, default=DEFAULT_MIN_SOC): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
            vol.Required(CONF_GRID_TARGET, default=DEFAULT_GRID_TARGET): vol.Coerce(float),
            vol.Required(CONF_GRID_DEADBAND, default=DEFAULT_GRID_DEADBAND): vol.All(vol.Coerce(float), vol.Range(min=0)),
        })
        return self.async_show_form(step_id="user", data_schema=schema)
