from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_GRID_METER_AVAILABLE,
    ATTR_HYPER_AVAILABLE,
    ATTR_SOLARFLOW_AVAILABLE,
    DOMAIN,
    VERSION,
)

HEALTH_ENTITIES = [
    ("grid_meter_health", "Grid Meter Health", ATTR_GRID_METER_AVAILABLE),
    ("hyper_health", "Hyper 2000 Health", ATTR_HYPER_AVAILABLE),
    ("solarflow_health", "SolarFlow 2400 Pro Health", ATTR_SOLARFLOW_AVAILABLE),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [CarpiquetHealthSensor(coordinator, entry, *item) for item in HEALTH_ENTITIES]
    )


class CarpiquetHealthSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, key, name, data_key):
        super().__init__(coordinator)
        self._entry = entry
        self._data_key = data_key
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = "mdi:check-network-outline"

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self._data_key))

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Carpiquet EMS",
            "manufacturer": "Carpiquet EMS",
            "model": "Dual Zendure Energy Manager",
            "sw_version": VERSION,
        }
