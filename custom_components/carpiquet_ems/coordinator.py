from datetime import timedelta
import logging
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .algorithm import BatteryState, allocate_discharge_power
from .const import *

_LOGGER=logging.getLogger(__name__)

class CarpiquetEMSCoordinator(DataUpdateCoordinator):
    def __init__(self,hass,config_entry):
        self.config=config_entry.data|config_entry.options
        self._previous_simulated_power=0.0
        super().__init__(hass,_LOGGER,name="Carpiquet EMS",
                         update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))

    def _state(self,eid):
        return self.hass.states.get(eid)

    def _is_available(self,eid):
        s=self._state(eid)
        return bool(s and s.state not in (STATE_UNKNOWN,STATE_UNAVAILABLE,None,""))

    def _state_float(self,eid,default=0.0):
        s=self._state(eid)
        if not s or s.state in (STATE_UNKNOWN,STATE_UNAVAILABLE): return default
        try: return float(s.state)
        except (TypeError,ValueError): return default

    async def _async_update_data(self):
        try:
            ge=self.config[CONF_GRID_POWER_ENTITY]
            hse=self.config[CONF_HYPER_SOC_ENTITY]
            sse=self.config[CONF_SOLARFLOW_SOC_ENTITY]
            hpe=self.config[CONF_HYPER_PV_ENTITY]
            spe=self.config[CONF_SOLARFLOW_PV_ENTITY]

            gok=self._is_available(ge)
            hok=self._is_available(hse) and self._is_available(hpe)
            sok=self._is_available(sse) and self._is_available(spe)

            grid=self._state_float(ge)
            hs=self._state_float(hse); ss=self._state_float(sse)
            hpv=self._state_float(hpe); spv=self._state_float(spe)
            target=float(self.config[CONF_GRID_TARGET])
            deadband=float(self.config[CONF_GRID_DEADBAND])
            min_soc=float(self.config[CONF_MIN_SOC])
            ramp=float(self.config.get(CONF_RAMP_LIMIT_W,DEFAULT_RAMP_LIMIT_W))

            error=grid-target
            requested=error if gok and error>deadband else 0.0
            r=allocate_discharge_power(
                requested,
                BatteryState(hs,float(self.config[CONF_HYPER_CAPACITY_KWH]),float(self.config[CONF_HYPER_MAX_POWER_W]),hok),
                BatteryState(ss,float(self.config[CONF_SOLARFLOW_CAPACITY_KWH]),float(self.config[CONF_SOLARFLOW_MAX_POWER_W]),sok),
                min_soc,self._previous_simulated_power,ramp)
            total=r.hyper_power_w+r.solarflow_power_w
            self._previous_simulated_power=total
            health=round(sum([gok,hok,sok])/3*100)
            status="healthy" if health==100 else "warning" if health>=67 else "critical"

            return {
                ATTR_GRID_POWER:round(grid,1), ATTR_REQUESTED_DISCHARGE:round(requested,1),
                ATTR_EFFECTIVE_REQUEST:r.effective_request_w, ATTR_UNSERVED_POWER:r.unserved_power_w,
                ATTR_HYPER_SOC:round(hs,1), ATTR_SOLARFLOW_SOC:round(ss,1),
                ATTR_HYPER_PV:round(hpv,1), ATTR_SOLARFLOW_PV:round(spv,1),
                ATTR_HYPER_SIMULATED:r.hyper_power_w, ATTR_SOLARFLOW_SIMULATED:r.solarflow_power_w,
                ATTR_TOTAL_SIMULATED:round(total,1), ATTR_SIMULATED_GRID:round(grid-total,1),
                ATTR_BALANCE_INDEX:r.balance_index_percent,
                ATTR_HYPER_AVAILABLE_POWER:r.hyper_available_power_w,
                ATTR_SOLARFLOW_AVAILABLE_POWER:r.solarflow_available_power_w,
                ATTR_TOTAL_AVAILABLE_POWER:r.total_available_power_w,
                ATTR_ACTIVE_BATTERIES:r.active_batteries,
                ATTR_DISPATCH_MODE:"energy_weighted_balanced",
                ATTR_LIMIT_REASON:r.limit_reason,
                ATTR_HEALTH_SCORE:health, ATTR_SYSTEM_STATUS:status,
                ATTR_GRID_METER_AVAILABLE:gok, ATTR_HYPER_AVAILABLE:hok, ATTR_SOLARFLOW_AVAILABLE:sok,
            }
        except Exception as err:
            raise UpdateFailed(f"Unable to calculate EMS state: {err}") from err
