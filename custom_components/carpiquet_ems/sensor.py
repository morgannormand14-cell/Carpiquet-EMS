from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

SENSORS = [
    ("engine_initialization_state", "Engine Initialization State", ATTR_ENGINE_INITIALIZATION_STATE, None, None),
    ("engine_initialization_error", "Engine Initialization Error", ATTR_ENGINE_INITIALIZATION_ERROR, None, None),
    ("session_recording_state", "Recording State", ATTR_SESSION_RECORDING_STATE, None, None),
    ("session_save_error", "Session Save Error", ATTR_SESSION_SAVE_ERROR, None, None),
    ("last_session_ended_at", "Last Session Ended At", ATTR_LAST_SESSION_ENDED_AT, None, None),
    ("house_load_raw", "House Load Raw", ATTR_HOUSE_LOAD_RAW, "W", "power"),
    ("performance_average", "Performance Average", ATTR_PERFORMANCE_AVERAGE, "%", None),
    ("zendure_average", "Zendure Average", ATTR_ZENDURE_AVERAGE, "%", None),
    ("real_import_energy", "Real Import Energy", ATTR_REAL_IMPORT_ENERGY, "kWh", "energy"),
    ("real_export_energy", "Real Export Energy", ATTR_REAL_EXPORT_ENERGY, "kWh", "energy"),
    ("sim_import_energy", "Sim Import Energy", ATTR_SIM_IMPORT_ENERGY, "kWh", "energy"),
    ("sim_export_energy", "Sim Export Energy", ATTR_SIM_EXPORT_ENERGY, "kWh", "energy"),
    ("pv_charged_energy", "PV Charged Energy", ATTR_PV_CHARGED_ENERGY, "kWh", "energy"),
    ("pv_curtailed_energy", "PV Curtailed Energy", ATTR_PV_CURTAILED_ENERGY, "kWh", "energy"),
    ("pv_curtailed", "PV Curtailed", ATTR_PV_CURTAILED, "W", "power"),
    ("grid_export_block_reason", "Grid Export Block Reason", ATTR_GRID_EXPORT_BLOCK_REASON, None, None),
    ("full_systems_count", "Full Systems Count", ATTR_FULL_SYSTEMS_COUNT, None, None),
    ("hyper_pv_to_home", "Hyper PV To Home", ATTR_HYPER_PV_TO_HOME, "W", "power"),
    ("solarflow_pv_to_home", "SolarFlow PV To Home", ATTR_SOLARFLOW_PV_TO_HOME, "W", "power"),
    ("hyper_battery_discharge", "Hyper Battery Discharge", ATTR_HYPER_BATTERY_DISCHARGE, "W", "power"),
    ("solarflow_battery_discharge", "SolarFlow Battery Discharge", ATTR_SOLARFLOW_BATTERY_DISCHARGE, "W", "power"),
    ("real_hyper_grid_input", "Real Hyper Grid Input", ATTR_REAL_HYPER_GRID_INPUT, "W", "power"),
    ("real_solarflow_grid_input", "Real SolarFlow Grid Input", ATTR_REAL_SOLARFLOW_GRID_INPUT, "W", "power"),
    ("selected_report", "Selected Report", ATTR_SELECTED_REPORT, None, None),
    ("report_download_url", "Report Download URL", ATTR_REPORT_DOWNLOAD_URL, None, None),
    ("session_id", "Session ID", ATTR_SESSION_ID, None, None),
    ("session_started_at", "Session Started At", ATTR_SESSION_STARTED_AT, None, None),
    ("session_duration", "Session Duration", ATTR_SESSION_DURATION, "s", "duration"),
    ("session_sample_count", "Session Sample Count", ATTR_SESSION_SAMPLE_COUNT, None, None),
    ("last_session_file", "Last Session File", ATTR_LAST_SESSION_FILE, None, None),
    ("house_load", "House Load", ATTR_HOUSE_LOAD, "W", "power"),
    ("real_zendure_total_output", "Real Zendure Total Output", ATTR_REAL_ZENDURE_TOTAL_OUTPUT, "W", "power"),
    ("real_hyper_output", "Real Hyper Output", ATTR_REAL_HYPER_OUTPUT, "W", "power"),
    ("real_solarflow_output", "Real SolarFlow Output", ATTR_REAL_SOLARFLOW_OUTPUT, "W", "power"),
    ("sim_hyper_home", "Sim Hyper Home", ATTR_SIM_HYPER_HOME, "W", "power"),
    ("sim_solarflow_home", "Sim SolarFlow Home", ATTR_SIM_SOLARFLOW_HOME, "W", "power"),
    ("sim_hyper_charge", "Sim Hyper Charge", ATTR_SIM_HYPER_CHARGE, "W", "power"),
    ("sim_solarflow_charge", "Sim SolarFlow Charge", ATTR_SIM_SOLARFLOW_CHARGE, "W", "power"),
    ("sim_hyper_export_pool", "Sim Hyper Export Pool", ATTR_SIM_HYPER_EXPORT_POOL, "W", "power"),
    ("sim_solarflow_export_pool", "Sim SolarFlow Export Pool", ATTR_SIM_SOLARFLOW_EXPORT_POOL, "W", "power"),
    ("sim_cross_charge_hyper", "Sim Cross Charge Hyper", ATTR_SIM_CROSS_CHARGE_HYPER, "W", "power"),
    ("sim_cross_charge_solarflow", "Sim Cross Charge SolarFlow", ATTR_SIM_CROSS_CHARGE_SOLARFLOW, "W", "power"),
    ("sim_grid_final", "Sim Grid Final", ATTR_SIM_GRID_FINAL, "W", "power"),
    ("real_grid_error", "Real Grid Error", ATTR_REAL_GRID_ERROR, "W", "power"),
    ("sim_grid_error", "Sim Grid Error", ATTR_SIM_GRID_ERROR, "W", "power"),
    ("performance_score", "Performance Score", ATTR_PERFORMANCE_SCORE, "%", None),
    ("zendure_reference_score", "Zendure Reference Score", ATTR_ZENDURE_REFERENCE_SCORE, "%", None),
    ("performance_gain", "Performance Gain", ATTR_PERFORMANCE_GAIN, "points", None),
    ("virtual_hyper_energy", "Virtual Hyper Energy", ATTR_VIRTUAL_HYPER_ENERGY, "kWh", "energy"),
    ("virtual_solarflow_energy", "Virtual SolarFlow Energy", ATTR_VIRTUAL_SOLARFLOW_ENERGY, "kWh", "energy"),
    ("virtual_hyper_soc", "Virtual Hyper SOC", ATTR_VIRTUAL_HYPER_SOC, "%", "battery"),
    ("virtual_solarflow_soc", "Virtual SolarFlow SOC", ATTR_VIRTUAL_SOLARFLOW_SOC, "%", "battery"),
    ("pv_total", "PV Total", ATTR_PV_TOTAL, "W", "power"),
    ("solar_surplus", "Solar Surplus", ATTR_SOLAR_SURPLUS, "W", "power"),
    ("operation_mode", "Operation Mode", ATTR_OPERATION_MODE, None, None),
    ("performance_sample_count", "Performance Sample Count", ATTR_PERF_SAMPLE_COUNT, None, None),
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
