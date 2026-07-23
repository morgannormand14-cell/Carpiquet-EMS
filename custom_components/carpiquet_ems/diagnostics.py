from homeassistant.components.diagnostics import async_redact_data
from .const import DOMAIN

async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "version": "0.3.0-alpha-sprint2",
        "mode": "simulation_only",
        "config": async_redact_data(dict(entry.data), set()),
        "state": coordinator.data,
    }
