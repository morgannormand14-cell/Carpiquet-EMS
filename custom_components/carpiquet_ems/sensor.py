from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

SENSORS = [
    ("grid_power", "Grid Power", ATTR_GRID_POWER, "W", "power"),
    ("requested_discharge", "Requested Discharge", ATTR_REQUESTED_DISCHARGE, "W", "power"),
    ("effective_request", "Effective Request", ATTR_EFFECTIVE_REQUEST, "W", "power"),
    ("unserved_power", "Unserved Power", ATTR_UNSERVED_POWER, "W", "power"),
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
    ("hyper_available_power", "Hyper 2000 Available Power", ATTR_HYPER_AVAILABLE_POWER, "W", "power"),
    ("solarflow_available_power", "SolarFlow 2400 Pro Available Power", ATTR_SOLARFLOW_AVAILABLE_POWER, "W", "power"),
    ("total_available_power", "Total Available Power", ATTR_TOTAL_AVAILABLE_POWER, "W", "power"),
    ("active_batteries", "Active Batteries", ATTR_ACTIVE_BATTERIES, None, None),
    ("total_batteries", "Total Batteries", ATTR_TOTAL_BATTERIES, None, None),
    ("total_battery_capacity", "Total Battery Capacity", ATTR_TOTAL_CAPACITY, "kWh", "energy"),
    ("average_battery_soc", "Average Battery SOC", ATTR_AVERAGE_SOC, "%", "battery"),
    ("data_mode", "Data Mode", ATTR_DATA_MODE, None, None),
    ("fallback_active_count", "Fallback Active Count", ATTR_FALLBACK_ACTIVE_COUNT, None, None),
    ("last_fallback_sync", "Last Fallback Sync", ATTR_LAST_FALLBACK_SYNC, None, None),
    ("dispatch_mode", "Dispatch Mode", ATTR_DISPATCH_MODE, None, None),
    ("limit_reason", "Limit Reason", ATTR_LIMIT_REASON, None, None),
    ("hyper_capacity", "Hyper 2000 Capacity", ATTR_HYPER_CAPACITY, "kWh", "energy"),
    ("solarflow_capacity", "SolarFlow 2400 Pro Capacity", ATTR_SOLARFLOW_CAPACITY, "kWh", "energy"),
    ("hyper_max_power", "Hyper 2000 Max Power", ATTR_HYPER_MAX_POWER, "W", "power"),
    ("solarflow_max_power", "SolarFlow 2400 Pro Max Power", ATTR_SOLARFLOW_MAX_POWER, "W", "power"),
    ("hyper_min_soc", "Hyper 2000 Min SOC", ATTR_HYPER_MIN_SOC, "%", "battery"),
    ("hyper_max_soc", "Hyper 2000 Max SOC", ATTR_HYPER_MAX_SOC, "%", "battery"),
    ("solarflow_min_soc", "SolarFlow 2400 Pro Min SOC", ATTR_SOLARFLOW_MIN_SOC, "%", "battery"),
    ("solarflow_max_soc", "SolarFlow 2400 Pro Max SOC", ATTR_SOLARFLOW_MAX_SOC, "%", "battery"),
    ("automation_state", "Automation State", ATTR_AUTOMATION_STATE, None, None),
    ("automation_reason", "Automation Reason", ATTR_AUTOMATION_REASON, None, None),
    ("automation_request", "Automation Request", ATTR_AUTOMATION_REQUEST_W, "W", "power"),
    ("automation_cycle", "Automation Cycle", ATTR_AUTOMATION_CYCLE, None, None),
    ("automation_last_transition", "Automation Last Transition", ATTR_AUTOMATION_LAST_TRANSITION, None, None),
    ("automation_hold_remaining", "Automation Hold Remaining", ATTR_AUTOMATION_HOLD_REMAINING, "s", "duration"),
    ("automation_policy", "Automation Policy", ATTR_AUTOMATION_POLICY, None, None),
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
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Carpiquet EMS",
            "manufacturer": "Carpiquet EMS",
            "model": "Dual Zendure Energy Manager",
            "sw_version": VERSION,
        }

    @property
    def extra_state_attributes(self):
        if self._data_key == ATTR_DATA_MODE:
            return {
                "sources": self.coordinator.data.get(ATTR_DYNAMIC_SOURCES, {}),
                "fallbacks": self.coordinator.data.get(ATTR_FALLBACKS, {}),
                "last_sync": self.coordinator.data.get(ATTR_LAST_FALLBACK_SYNC),
            }
        return {"mode": "simulation", "version": VERSION}
