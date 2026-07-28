from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

BINARY_SENSORS = [
    ("automation_safety_gate", "Automation Safety Gate", ATTR_AUTOMATION_SAFETY_OK),
    ("grid_meter_health", "Grid Meter Health", ATTR_GRID_METER_AVAILABLE),
    ("hyper_2000_health", "Hyper 2000 Health", ATTR_HYPER_AVAILABLE),
    ("solarflow_2400_pro_health", "SolarFlow 2400 Pro Health", ATTR_SOLARFLOW_AVAILABLE),
    ("simulation_session_active", "Simulation Session Active", ATTR_SESSION_ACTIVE),
]

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CarpiquetBinarySensor(coordinator, entry, *item) for item in BINARY_SENSORS])

class CarpiquetBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, key, name, data_key):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self._data_key, False))
