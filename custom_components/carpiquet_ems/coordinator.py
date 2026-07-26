from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .algorithm import BatteryState, allocate_discharge_power
from .const import *
from .topology import valid_numeric

_LOGGER = logging.getLogger(__name__)

DYNAMIC = {
    "hyper_capacity": (CONF_HYPER_CAPACITY_ENTITY, CONF_FALLBACK_HYPER_CAPACITY, 0.1, 100.0),
    "solarflow_capacity": (CONF_SOLARFLOW_CAPACITY_ENTITY, CONF_FALLBACK_SOLARFLOW_CAPACITY, 0.1, 100.0),
    "hyper_max_power": (CONF_HYPER_MAX_POWER_ENTITY, CONF_FALLBACK_HYPER_MAX_POWER, 1.0, 10000.0),
    "solarflow_max_power": (CONF_SOLARFLOW_MAX_POWER_ENTITY, CONF_FALLBACK_SOLARFLOW_MAX_POWER, 1.0, 10000.0),
    "hyper_min_soc": (CONF_HYPER_MIN_SOC_ENTITY, CONF_FALLBACK_HYPER_MIN_SOC, 0.0, 100.0),
    "hyper_max_soc": (CONF_HYPER_MAX_SOC_ENTITY, CONF_FALLBACK_HYPER_MAX_SOC, 0.0, 100.0),
    "solarflow_min_soc": (CONF_SOLARFLOW_MIN_SOC_ENTITY, CONF_FALLBACK_SOLARFLOW_MIN_SOC, 0.0, 100.0),
    "solarflow_max_soc": (CONF_SOLARFLOW_MAX_SOC_ENTITY, CONF_FALLBACK_SOLARFLOW_MAX_SOC, 0.0, 100.0),
}

class CarpiquetEMSCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        self.entry = config_entry
        self.config = config_entry.data | config_entry.options
        self._previous_simulated_power = 0.0
        self._fallbacks = {
            fallback_key: self.config.get(fallback_key)
            for _, fallback_key, _, _ in DYNAMIC.values()
        }
        self._last_fallback_sync = None
        self._store = Store(hass, 1, f"{DOMAIN}.{config_entry.entry_id}.fallbacks")
        super().__init__(
            hass,
            _LOGGER,
            name="Carpiquet EMS",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def async_initialize(self):
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            values = stored.get("values")
            if isinstance(values, dict):
                self._fallbacks.update(values)
            self._last_fallback_sync = stored.get("last_sync")

    def _state(self, entity_id):
        return self.hass.states.get(entity_id)

    def _is_available(self, entity_id):
        state = self._state(entity_id)
        return bool(state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, None, ""))

    def _state_float(self, entity_id, default=0.0):
        state = self._state(entity_id)
        if not state or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return default
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return default

    async def _dynamic_values(self):
        result = {}
        sources = {}
        changed = False
        fallback_count = 0

        for name, (entity_key, fallback_key, minimum, maximum) in DYNAMIC.items():
            entity_id = self.config[entity_key]
            state = self._state(entity_id)
            live = None
            if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE, "", None):
                try:
                    candidate = float(state.state)
                    if valid_numeric(candidate, minimum, maximum):
                        live = candidate
                except (TypeError, ValueError):
                    pass

            if live is not None:
                result[name] = live
                sources[name] = "live"
                old = self._fallbacks.get(fallback_key)
                if old is None or abs(float(old) - live) > 0.0001:
                    self._fallbacks[fallback_key] = live
                    changed = True
            else:
                fallback = self._fallbacks.get(fallback_key)
                if fallback is None:
                    raise UpdateFailed(f"No live or fallback value for {name}")
                result[name] = float(fallback)
                sources[name] = "fallback"
                fallback_count += 1

        if changed:
            self._last_fallback_sync = datetime.now(timezone.utc).isoformat()
            await self._store.async_save({
                "values": self._fallbacks,
                "last_sync": self._last_fallback_sync,
            })

        return result, sources, fallback_count

    def _battery_status(self):
        batteries = self.config.get(CONF_BATTERIES, [])
        active = 0
        soc_values = []
        for battery in batteries:
            entity_id = battery.get(CONF_BATTERY_ENTITIES, {}).get("soc_level")
            if not entity_id:
                continue
            state = self._state(entity_id)
            if not state or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, "", None):
                continue
            try:
                soc = float(state.state)
            except (TypeError, ValueError):
                continue
            if 0 <= soc <= 100:
                active += 1
                soc_values.append(soc)
        return len(batteries), active, soc_values

    async def _async_update_data(self):
        try:
            dynamic, sources, fallback_count = await self._dynamic_values()

            grid_entity = self.config[CONF_GRID_POWER_ENTITY]
            hyper_soc_entity = self.config[CONF_HYPER_SOC_ENTITY]
            solar_soc_entity = self.config[CONF_SOLARFLOW_SOC_ENTITY]
            hyper_pv_entity = self.config[CONF_HYPER_PV_ENTITY]
            solar_pv_entity = self.config[CONF_SOLARFLOW_PV_ENTITY]

            grid_ok = self._is_available(grid_entity)
            hyper_ok = self._is_available(hyper_soc_entity) and self._is_available(hyper_pv_entity)
            solar_ok = self._is_available(solar_soc_entity) and self._is_available(solar_pv_entity)

            grid = self._state_float(grid_entity)
            hyper_soc = self._state_float(hyper_soc_entity)
            solar_soc = self._state_float(solar_soc_entity)
            hyper_pv = self._state_float(hyper_pv_entity)
            solar_pv = self._state_float(solar_pv_entity)

            target = float(self.config.get(CONF_GRID_TARGET, DEFAULT_GRID_TARGET))
            deadband = float(self.config.get(CONF_GRID_DEADBAND, DEFAULT_GRID_DEADBAND))
            ramp = float(self.config.get(CONF_RAMP_LIMIT_W, DEFAULT_RAMP_LIMIT_W))

            error = grid - target
            requested = error if grid_ok and error > deadband else 0.0

            result = allocate_discharge_power(
                requested,
                BatteryState(
                    hyper_soc,
                    dynamic["hyper_capacity"],
                    dynamic["hyper_max_power"],
                    hyper_ok,
                ),
                BatteryState(
                    solar_soc,
                    dynamic["solarflow_capacity"],
                    dynamic["solarflow_max_power"],
                    solar_ok,
                ),
                # Algorithm currently accepts one reserve. Use the stricter live reserve;
                # per-device reserve enforcement is additionally applied by availability.
                max(dynamic["hyper_min_soc"], dynamic["solarflow_min_soc"]),
                previous_power_w=self._previous_simulated_power,
                ramp_limit_w=ramp,
            )

            # Device-specific hard reserve override.
            hyper_power = result.hyper_power_w if hyper_soc > dynamic["hyper_min_soc"] else 0.0
            solar_power = result.solarflow_power_w if solar_soc > dynamic["solarflow_min_soc"] else 0.0
            total = hyper_power + solar_power
            self._previous_simulated_power = total

            total_batteries, active_batteries, physical_socs = self._battery_status()
            total_capacity = dynamic["hyper_capacity"] + dynamic["solarflow_capacity"]
            if total_capacity > 0:
                average_soc = (
                    hyper_soc * dynamic["hyper_capacity"]
                    + solar_soc * dynamic["solarflow_capacity"]
                ) / total_capacity
            elif physical_socs:
                average_soc = sum(physical_socs) / len(physical_socs)
            else:
                average_soc = 0.0

            health = round(sum([grid_ok, hyper_ok, solar_ok]) / 3 * 100)
            status = "healthy" if health == 100 else "warning" if health >= 67 else "critical"

            return {
                ATTR_GRID_POWER: round(grid, 1),
                ATTR_REQUESTED_DISCHARGE: round(requested, 1),
                ATTR_EFFECTIVE_REQUEST: result.effective_request_w,
                ATTR_UNSERVED_POWER: round(max(0.0, result.effective_request_w - total), 1),
                ATTR_HYPER_SOC: round(hyper_soc, 1),
                ATTR_SOLARFLOW_SOC: round(solar_soc, 1),
                ATTR_HYPER_PV: round(hyper_pv, 1),
                ATTR_SOLARFLOW_PV: round(solar_pv, 1),
                ATTR_HYPER_SIMULATED: round(hyper_power, 1),
                ATTR_SOLARFLOW_SIMULATED: round(solar_power, 1),
                ATTR_TOTAL_SIMULATED: round(total, 1),
                ATTR_SIMULATED_GRID: round(grid - total, 1),
                ATTR_BALANCE_INDEX: result.balance_index_percent,
                ATTR_HYPER_AVAILABLE_POWER: dynamic["hyper_max_power"] if hyper_ok and hyper_soc > dynamic["hyper_min_soc"] else 0.0,
                ATTR_SOLARFLOW_AVAILABLE_POWER: dynamic["solarflow_max_power"] if solar_ok and solar_soc > dynamic["solarflow_min_soc"] else 0.0,
                ATTR_TOTAL_AVAILABLE_POWER: (
                    (dynamic["hyper_max_power"] if hyper_ok and hyper_soc > dynamic["hyper_min_soc"] else 0.0)
                    + (dynamic["solarflow_max_power"] if solar_ok and solar_soc > dynamic["solarflow_min_soc"] else 0.0)
                ),
                ATTR_ACTIVE_BATTERIES: active_batteries,
                ATTR_TOTAL_BATTERIES: total_batteries,
                ATTR_TOTAL_CAPACITY: round(total_capacity, 3),
                ATTR_AVERAGE_SOC: round(average_soc, 1),
                ATTR_DATA_MODE: "LIVE" if fallback_count == 0 else "FALLBACK ACTIF",
                ATTR_FALLBACK_ACTIVE_COUNT: fallback_count,
                ATTR_LAST_FALLBACK_SYNC: self._last_fallback_sync or "never",
                ATTR_DISPATCH_MODE: "energy_weighted_balanced",
                ATTR_LIMIT_REASON: result.limit_reason,
                ATTR_HEALTH_SCORE: health,
                ATTR_SYSTEM_STATUS: status,
                ATTR_GRID_METER_AVAILABLE: grid_ok,
                ATTR_HYPER_AVAILABLE: hyper_ok,
                ATTR_SOLARFLOW_AVAILABLE: solar_ok,
                ATTR_HYPER_CAPACITY: round(dynamic["hyper_capacity"], 3),
                ATTR_SOLARFLOW_CAPACITY: round(dynamic["solarflow_capacity"], 3),
                ATTR_HYPER_MAX_POWER: round(dynamic["hyper_max_power"], 1),
                ATTR_SOLARFLOW_MAX_POWER: round(dynamic["solarflow_max_power"], 1),
                ATTR_HYPER_MIN_SOC: round(dynamic["hyper_min_soc"], 1),
                ATTR_HYPER_MAX_SOC: round(dynamic["hyper_max_soc"], 1),
                ATTR_SOLARFLOW_MIN_SOC: round(dynamic["solarflow_min_soc"], 1),
                ATTR_SOLARFLOW_MAX_SOC: round(dynamic["solarflow_max_soc"], 1),
                ATTR_DYNAMIC_SOURCES: sources,
                ATTR_FALLBACKS: dict(self._fallbacks),
            }
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Unable to calculate EMS state: {err}") from err
