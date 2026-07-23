DOMAIN = "carpiquet_ems"
VERSION = "0.3.0-alpha-sprint2"
DEFAULT_SCAN_INTERVAL = 2

CONF_GRID_POWER_ENTITY = "grid_power_entity"
CONF_HYPER_SOC_ENTITY = "hyper_soc_entity"
CONF_HYPER_PV_ENTITY = "hyper_pv_entity"
CONF_HYPER_OUTPUT_ENTITY = "hyper_output_entity"
CONF_SOLARFLOW_SOC_ENTITY = "solarflow_soc_entity"
CONF_SOLARFLOW_PV_ENTITY = "solarflow_pv_entity"
CONF_SOLARFLOW_OUTPUT_ENTITY = "solarflow_output_entity"
CONF_HYPER_CAPACITY_KWH = "hyper_capacity_kwh"
CONF_SOLARFLOW_CAPACITY_KWH = "solarflow_capacity_kwh"
CONF_HYPER_MAX_POWER_W = "hyper_max_power_w"
CONF_SOLARFLOW_MAX_POWER_W = "solarflow_max_power_w"
CONF_MIN_SOC = "minimum_soc"
CONF_GRID_TARGET = "grid_target"
CONF_GRID_DEADBAND = "grid_deadband"

DEFAULT_HYPER_CAPACITY_KWH = 3.84
DEFAULT_SOLARFLOW_CAPACITY_KWH = 5.28
DEFAULT_HYPER_MAX_POWER_W = 1200.0
DEFAULT_SOLARFLOW_MAX_POWER_W = 2400.0
DEFAULT_MIN_SOC = 10.0
DEFAULT_GRID_TARGET = 0.0
DEFAULT_GRID_DEADBAND = 20.0

ATTR_GRID_POWER = "grid_power_w"
ATTR_REQUESTED_DISCHARGE = "requested_discharge_w"
ATTR_HYPER_SOC = "hyper_soc_percent"
ATTR_SOLARFLOW_SOC = "solarflow_soc_percent"
ATTR_HYPER_PV = "hyper_pv_w"
ATTR_SOLARFLOW_PV = "solarflow_pv_w"
ATTR_HYPER_SIMULATED = "hyper_simulated_power_w"
ATTR_SOLARFLOW_SIMULATED = "solarflow_simulated_power_w"
ATTR_TOTAL_SIMULATED = "total_simulated_power_w"
ATTR_SIMULATED_GRID = "simulated_grid_power_w"
ATTR_BALANCE_INDEX = "balance_index_percent"

ATTR_HEALTH_SCORE = "health_score_percent"
ATTR_SYSTEM_STATUS = "system_status"
ATTR_GRID_METER_AVAILABLE = "grid_meter_available"
ATTR_HYPER_AVAILABLE = "hyper_available"
ATTR_SOLARFLOW_AVAILABLE = "solarflow_available"
ATTR_LAST_UPDATE_AGE = "last_update_age_seconds"
