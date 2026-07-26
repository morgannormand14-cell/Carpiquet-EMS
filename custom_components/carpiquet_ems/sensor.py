from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import *

SENSORS = [
    ("grid_power", "Grid Power", ATTR_GRID_POWER, "W", "power"),
    ("requested_discharge", "Requested Discharge", ATTR_REQUESTED_DISCHARGE, "W", "power"),
    ("hyper_2000_soc", "Hyper 2000 SOC", ATTR_HYPER_SOC, "%", "battery"),
    ("solarflow_2400_pro_soc", "SolarFlow 2400 Pro SOC", ATTR_SOLARFLOW_SOC, "%", "battery"),
    ("hyper_2000_pv_power", "Hyper 2000 PV Power", ATTR_HYPER_PV, "W", "power"),
    ("solarflow_2400_pro_pv_power", "SolarFlow 2400 Pro PV Power", ATTR_SOLARFLOW_PV, "W", "power"),
    ("hyper_2000_simulated_power", "Hyper 2000 Simulated Power", ATTR_HYPER_SIMULATED, "W", "power"),
    ("solarflow_2400_pro_simulated_power", "SolarFlow 2400 Pro Simulated Power", ATTR_SOLARFLOW_SIMULATED, "W", "power"),
    ("total_simulated_battery_power", "Total Simulated Battery Power", ATTR_TOTAL_SIMULATED, "W", "power"),
    ("simulated_grid_power", "Simulated Grid Power", ATTR_SIMULATED_GRID, "W", "power"),
    ("battery_balance_index", "Battery Balance Index", ATTR_BALANCE_INDEX, "%", None),
    ("health_score", "Health Score", ATTR_HEALTH_SCORE, "%", None),
    ("system_status", "System Status", ATTR_SYSTEM_STATUS, None, None),
    ("effective_request", "Effective Request", ATTR_EFFECTIVE_REQUEST, "W", "power"),
    ("unserved_power", "Unserved Power", ATTR_UNSERVED_POWER, "W", "power"),
    ("hyper_available_power", "Hyper 2000 Available Power", ATTR_HYPER_AVAILABLE_POWER, "W", "power"),
    ("solarflow_available_power", "SolarFlow 2400 Pro Available Power", ATTR_SOLARFLOW_AVAILABLE_POWER, "W", "power"),
    ("total_available_power", "Total Available Power", ATTR_TOTAL_AVAILABLE_POWER, "W", "power"),
    ("active_batteries", "Active Batteries", ATTR_ACTIVE_BATTERIES, None, None),
    ("dispatch_mode", "Dispatch Mode", ATTR_DISPATCH_MODE, None, None),
    ("limit_reason", "Limit Reason", ATTR_LIMIT_REASON, None, None),
]

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CarpiquetSensor(coordinator, entry, *item) for item in SENSORS])

class CarpiquetSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name, data_key, unit, device_class):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._data_key = data_key

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key)

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._entry.entry_id)}, "name": "Carpiquet EMS", "manufacturer": "Carpiquet EMS", "model": "Dual Zendure Energy Manager", "sw_version": VERSION}

    @property
    def extra_state_attributes(self):
        return {"mode": "simulation", "version": VERSION, **self.coordinator.data}
