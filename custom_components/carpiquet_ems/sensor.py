from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

SENSORS = [
    ("grid_power", "Grid Power", ATTR_GRID_POWER, "W", "power"),
    ("requested_discharge", "Requested Discharge", ATTR_REQUESTED_DISCHARGE, "W", "power"),
    ("hyper_soc", "Hyper 2000 SOC", ATTR_HYPER_SOC, "%", "battery"),
    ("solarflow_soc", "SolarFlow 2400 Pro SOC", ATTR_SOLARFLOW_SOC, "%", "battery"),
    ("hyper_pv_power", "Hyper 2000 PV Power", ATTR_HYPER_PV, "W", "power"),
    ("solarflow_pv_power", "SolarFlow 2400 Pro PV Power", ATTR_SOLARFLOW_PV, "W", "power"),
    ("hyper_simulated_power", "Hyper 2000 Simulated Power", ATTR_HYPER_SIMULATED, "W", "power"),
    ("solarflow_simulated_power", "SolarFlow 2400 Pro Simulated Power", ATTR_SOLARFLOW_SIMULATED, "W", "power"),
    ("total_simulated_power", "Total Simulated Battery Power", ATTR_TOTAL_SIMULATED, "W", "power"),
    ("simulated_grid_power", "Simulated Grid Power", ATTR_SIMULATED_GRID, "W", "power"),
    ("balance_index", "Battery Balance Index", ATTR_BALANCE_INDEX, "%", None),
]

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CarpiquetSensor(coordinator, entry, *item) for item in SENSORS])

class CarpiquetSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name, data_key, unit, device_class):
        super().__init__(coordinator)
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_entity_id = f"sensor.carpiquet_ems_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._data_key = data_key

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)

    @property
    def extra_state_attributes(self):
        return {
            "mode": "simulation",
            "version": "0.2.0-alpha",
            **self.coordinator.data,
        }
