from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EMSNumber(coordinator, entry, CONF_MIN_SOC, "Minimum SOC", 0, 100, 1),
        EMSNumber(coordinator, entry, CONF_GRID_TARGET, "Grid Target", -5000, 5000, 1),
        EMSNumber(coordinator, entry, CONF_GRID_DEADBAND, "Grid Deadband", 0, 500, 1),
    ])

class EMSNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry, key, name, minimum, maximum, step):
        super().__init__(coordinator)
        self._key = key
        self._entry = entry
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_entity_id = f"number.carpiquet_ems_{key}"
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step

    @property
    def native_value(self):
        return float(self._entry.options.get(self._key, self.coordinator.config.get(self._key, 0)))

    async def async_set_native_value(self, value):
        options = dict(self._entry.options)
        options[self._key] = value
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        self.coordinator.config[self._key] = value
        await self.coordinator.async_request_refresh()
