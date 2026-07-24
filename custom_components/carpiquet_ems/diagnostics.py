from homeassistant.components.diagnostics import async_redact_data
from .const import DOMAIN, VERSION

async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "version": VERSION,
        "mode": "simulation_only",
        "config": async_redact_data(dict(entry.data), set()),
        "options": async_redact_data(dict(entry.options), set()),
        "state": coordinator.data,
    }
