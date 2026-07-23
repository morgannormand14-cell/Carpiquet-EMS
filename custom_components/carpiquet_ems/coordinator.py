from datetime import timedelta
import logging

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .algorithm import BatteryState, allocate_discharge_power
from .const import *

_LOGGER = logging.getLogger(__name__)


class CarpiquetEMSCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        self.config = config_entry.data | config_entry.options
        super().__init__(
            hass,
            _LOGGER,
            name="Carpiquet EMS",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    def _state(self, entity_id):
        return self.hass.states.get(entity_id)

    def _is_available(self, entity_id):
        state = self._state(entity_id)
        return bool(
            state
            and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, "")
        )

    def _state_float(self, entity_id, default=0.0):
        state = self._state(entity_id)
        if not state or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return default
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return default

    async def _async_update_data(self):
        try:
            grid_entity = self.config[CONF_GRID_POWER_ENTITY]
            hyper_soc_entity = self.config[CONF_HYPER_SOC_ENTITY]
            solar_soc_entity = self.config[CONF_SOLARFLOW_SOC_ENTITY]
            hyper_pv_entity = self.config[CONF_HYPER_PV_ENTITY]
            solar_pv_entity = self.config[CONF_SOLARFLOW_PV_ENTITY]

            grid_available = self._is_available(grid_entity)
            hyper_available = (
                self._is_available(hyper_soc_entity)
                and self._is_available(hyper_pv_entity)
            )
            solar_available = (
                self._is_available(solar_soc_entity)
                and self._is_available(solar_pv_entity)
            )

            grid = self._state_float(grid_entity)
            hyper_soc = self._state_float(hyper_soc_entity)
            solar_soc = self._state_float(solar_soc_entity)
            hyper_pv = self._state_float(hyper_pv_entity)
            solar_pv = self._state_float(solar_pv_entity)

            target = float(self.config[CONF_GRID_TARGET])
            deadband = float(self.config[CONF_GRID_DEADBAND])
            minimum_soc = float(self.config[CONF_MIN_SOC])

            error = grid - target
            requested = error if grid_available and error > deadband else 0.0

            result = allocate_discharge_power(
                requested,
                BatteryState(
                    hyper_soc,
                    float(self.config[CONF_HYPER_CAPACITY_KWH]),
                    float(self.config[CONF_HYPER_MAX_POWER_W]),
                ),
                BatteryState(
                    solar_soc,
                    float(self.config[CONF_SOLARFLOW_CAPACITY_KWH]),
                    float(self.config[CONF_SOLARFLOW_MAX_POWER_W]),
                ),
                minimum_soc,
            )

            total = result.hyper_power_w + result.solarflow_power_w
            availability = [grid_available, hyper_available, solar_available]
            health_score = round(sum(availability) / len(availability) * 100)
            if health_score == 100:
                system_status = "healthy"
            elif health_score >= 67:
                system_status = "warning"
            else:
                system_status = "critical"

            return {
                ATTR_GRID_POWER: round(grid, 1),
                ATTR_REQUESTED_DISCHARGE: result.requested_power_w,
                ATTR_HYPER_SOC: round(hyper_soc, 1),
                ATTR_SOLARFLOW_SOC: round(solar_soc, 1),
                ATTR_HYPER_PV: round(hyper_pv, 1),
                ATTR_SOLARFLOW_PV: round(solar_pv, 1),
                ATTR_HYPER_SIMULATED: result.hyper_power_w,
                ATTR_SOLARFLOW_SIMULATED: result.solarflow_power_w,
                ATTR_TOTAL_SIMULATED: round(total, 1),
                ATTR_SIMULATED_GRID: round(grid - total, 1),
                ATTR_BALANCE_INDEX: result.balance_index_percent,
                ATTR_HEALTH_SCORE: health_score,
                ATTR_SYSTEM_STATUS: system_status,
                ATTR_GRID_METER_AVAILABLE: grid_available,
                ATTR_HYPER_AVAILABLE: hyper_available,
                ATTR_SOLARFLOW_AVAILABLE: solar_available,
            }
        except Exception as err:
            raise UpdateFailed(f"Unable to calculate EMS state: {err}") from err
