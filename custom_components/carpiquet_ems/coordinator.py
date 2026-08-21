from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio
import logging
from pathlib import Path
import shutil

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .algorithm import BatteryState, allocate_discharge_power
from .automation_engine import AutomationInput, POLICY, STATE_IDLE, decide_automation
from .digital_twin import TwinBattery, TwinInput, simulate_cycle
from .command_pipeline import CommandRequest, SafetyContext, evaluate_command
from .session_recorder import SimulationSessionRecorder
from .automation_engine import DISPLAY_REASON, DISPLAY_STATE
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
        self._shadow_cycle = 0
        self._shadow_accepted = 0
        self._shadow_rejected = 0
        self._automation_state = STATE_IDLE
        self._automation_cycle = 0
        self._automation_last_transition_dt = datetime.now(timezone.utc)
        self._virtual_hyper_energy_kwh = None
        self._virtual_solarflow_energy_kwh = None
        self._perf_samples = 0
        self._perf_score_sum = 0.0
        self._zendure_score_sum = 0.0
        self._real_import_kwh = 0.0
        self._real_export_kwh = 0.0
        self._sim_import_kwh = 0.0
        self._sim_export_kwh = 0.0
        self._pv_charged_kwh = 0.0
        self._pv_curtailed_kwh = 0.0
        self._last_cycle_dt = None
        self._twin_prev_hyper_discharge = 0.0
        self._twin_prev_solar_discharge = 0.0
        self._twin_prev_hyper_charge = 0.0
        self._twin_prev_solar_charge = 0.0
        self._session = SimulationSessionRecorder(hass, VERSION)
        self._session_stop_lock = asyncio.Lock()
        self._session_stopping = False
        self._initialization_state = "En attente"
        self._initialization_error = None
        self._initialization_ready = False
        self._automation_enabled_runtime = bool(self.config.get(CONF_AUTOMATION_ENABLED, DEFAULT_AUTOMATION_ENABLED))
        # Safety: every Home Assistant reload returns command control to Simulation.
        self._control_mode = CONTROL_MODE_SIMULATION
        self._shadow_cycle = 0
        self._shadow_accepted = 0
        self._shadow_rejected = 0
        self._selected_report = None
        self._report_download_url = None
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
        await self.hass.async_add_executor_job(self._session.finalize_orphaned_sessions)
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


    def _session_initial_state(self):
        return {
            "hyper_soc_percent": self._state_float(self.config[CONF_HYPER_SOC_ENTITY]),
            "solarflow_soc_percent": self._state_float(self.config[CONF_SOLARFLOW_SOC_ENTITY]),
            "grid_power_w": self._state_float(self.config[CONF_GRID_POWER_ENTITY]),
            "hyper_pv_w": self._state_float(self.config[CONF_HYPER_PV_ENTITY]),
            "solarflow_pv_w": self._state_float(self.config[CONF_SOLARFLOW_PV_ENTITY]),
            "hyper_real_output_w": self._state_float(self.config[CONF_HYPER_REAL_OUTPUT_ENTITY]),
            "solarflow_real_output_w": self._state_float(self.config[CONF_SOLARFLOW_REAL_OUTPUT_ENTITY]),
        }

    @property
    def automation_enabled(self):
        return bool(self._automation_enabled_runtime)

    async def async_set_automation_enabled(self, enabled: bool):
        enabled = bool(enabled)

        if enabled == self._automation_enabled_runtime:
            if enabled and not self._session.active and not self._session_stopping:
                await self.async_start_simulation_session()
            elif not enabled and (self._session.active or self._session.finalizing):
                await self.async_stop_simulation_session("runtime_reconcile")
            await self.async_request_refresh()
            return

        if not enabled:
            # Stop the simulated engine immediately. No later coordinator cycle
            # may append a sample after this boundary.
            self._automation_enabled_runtime = False
            self._session_stopping = True
            try:
                await self.async_stop_simulation_session("user_stop")
            finally:
                self._session_stopping = False
            self._initialization_state = "En attente"
            self._initialization_error = None
            self._initialization_ready = False
        else:
            self._automation_enabled_runtime = True
            started = await self.async_start_simulation_session()
            if not started:
                self._automation_enabled_runtime = False

        await self.async_request_refresh()

    def _session_initial_state(self):
        return {
            "hyper_soc_percent": self._state_float(self.config[CONF_HYPER_SOC_ENTITY]),
            "solarflow_soc_percent": self._state_float(self.config[CONF_SOLARFLOW_SOC_ENTITY]),
            "grid_power_w": self._state_float(self.config[CONF_GRID_POWER_ENTITY]),
            "hyper_pv_w": self._state_float(self.config[CONF_HYPER_PV_ENTITY]),
            "solarflow_pv_w": self._state_float(self.config[CONF_SOLARFLOW_PV_ENTITY]),
            "hyper_real_output_w": self._state_float(self.config[CONF_HYPER_REAL_OUTPUT_ENTITY]),
            "solarflow_real_output_w": self._state_float(self.config[CONF_SOLARFLOW_REAL_OUTPUT_ENTITY]),
            "hyper_grid_input_w": self._state_float(self.config.get(CONF_HYPER_GRID_INPUT_ENTITY, DEFAULT_HYPER_GRID_INPUT_ENTITY)),
            "solarflow_grid_input_w": self._state_float(self.config.get(CONF_SOLARFLOW_GRID_INPUT_ENTITY, DEFAULT_SOLARFLOW_GRID_INPUT_ENTITY)),
        }


    def _initialization_snapshot_is_valid(self, snapshot):
        # A real numeric 0% SOC is physically valid. Availability must be checked
        # from the Home Assistant states instead of inferring it from a 0.0 fallback.
        soc_entities = (
            self.config.get(CONF_HYPER_SOC_ENTITY),
            self.config.get(CONF_SOLARFLOW_SOC_ENTITY),
        )
        if not all(self._source_numeric_available(entity_id, 0.0, 100.0) for entity_id in soc_entities):
            return False, "SOC indisponible ou invalide"

        required_entities = (
            self.config.get(CONF_HYPER_CAPACITY_ENTITY),
            self.config.get(CONF_SOLARFLOW_CAPACITY_ENTITY),
            self.config.get(CONF_HYPER_MAX_POWER_ENTITY),
            self.config.get(CONF_SOLARFLOW_MAX_POWER_ENTITY),
            self.config.get(CONF_GRID_POWER_ENTITY),
        )
        missing = [
            entity_id
            for entity_id in required_entities
            if entity_id and self.hass.states.get(entity_id) is None
        ]
        if missing:
            return False, "Entités initiales indisponibles"

        return True, None

    async def _async_wait_for_valid_initialization(self, timeout_seconds=DEFAULT_INITIALIZATION_TIMEOUT_SECONDS):
        self._initialization_state = "Initialisation du moteur"
        self._initialization_error = None
        self._initialization_ready = False

        deadline = self.hass.loop.time() + float(timeout_seconds)
        last_snapshot = None
        last_error = "Données initiales indisponibles"

        while self.hass.loop.time() < deadline:
            last_snapshot = self._session_initial_state()
            valid, error = self._initialization_snapshot_is_valid(last_snapshot)
            if valid:
                self._initialization_state = "Prêt"
                self._initialization_ready = True
                self._initialization_error = None
                return last_snapshot
            last_error = error or last_error
            await asyncio.sleep(1)

        self._initialization_state = "Maintien de sécurité"
        self._initialization_ready = False
        self._initialization_error = last_error
        return None

    async def async_start_simulation_session(self):
        if self._session.active or self._session.finalizing:
            return True

        initial_state = await self._async_wait_for_valid_initialization()
        if initial_state is None:
            self._automation_enabled_runtime = False
            return False

        # Reset every session-scoped accumulator together. Keeping any value
        # from a previous session corrupts averages and energy totals.
        self._virtual_hyper_energy_kwh = None
        self._virtual_solarflow_energy_kwh = None
        self._previous_simulated_power = 0.0
        self._automation_cycle = 0
        self._perf_samples = 0
        self._perf_score_sum = 0.0
        self._zendure_score_sum = 0.0
        self._real_import_kwh = 0.0
        self._real_export_kwh = 0.0
        self._sim_import_kwh = 0.0
        self._sim_export_kwh = 0.0
        self._pv_charged_kwh = 0.0
        self._pv_curtailed_kwh = 0.0
        self._last_cycle_dt = None
        self._twin_prev_hyper_discharge = 0.0
        self._twin_prev_solar_discharge = 0.0
        self._twin_prev_hyper_charge = 0.0
        self._twin_prev_solar_charge = 0.0
        self._automation_state = STATE_IDLE
        self._automation_last_transition_dt = datetime.now(timezone.utc)

        safe_config = {
            key: value
            for key, value in self.config.items()
            if "token" not in key.lower() and "password" not in key.lower()
        }

        await self.hass.async_add_executor_job(
            self._session.start,
            initial_state,
            safe_config,
        )
        self._initialization_state = "Enregistrement actif"
        self._initialization_ready = True
        return True

    def _session_summary(self):
        data = self.data or {}
        return {
            "performance_score_percent": data.get(ATTR_PERFORMANCE_SCORE),
            "zendure_reference_score_percent": data.get(ATTR_ZENDURE_REFERENCE_SCORE),
            "performance_gain_points": data.get(ATTR_PERFORMANCE_GAIN),
            "real_grid_error_w": data.get(ATTR_REAL_GRID_ERROR),
            "sim_grid_error_w": data.get(ATTR_SIM_GRID_ERROR),
            "virtual_hyper_energy_kwh": data.get(ATTR_VIRTUAL_HYPER_ENERGY),
            "virtual_solarflow_energy_kwh": data.get(ATTR_VIRTUAL_SOLARFLOW_ENERGY),
            "performance_samples": data.get(ATTR_PERF_SAMPLE_COUNT),
            "performance_average_percent": round(self._perf_score_sum / self._perf_samples, 2) if self._perf_samples else None,
            "zendure_average_percent": round(self._zendure_score_sum / self._perf_samples, 2) if self._perf_samples else None,
            "real_import_energy_kwh": round(self._real_import_kwh, 4),
            "real_export_energy_kwh": round(self._real_export_kwh, 4),
            "sim_import_energy_kwh": round(self._sim_import_kwh, 4),
            "sim_export_energy_kwh": round(self._sim_export_kwh, 4),
            "pv_charged_energy_kwh": round(self._pv_charged_kwh, 4),
            "pv_curtailed_energy_kwh": round(self._pv_curtailed_kwh, 4),
        }

    async def async_stop_simulation_session(self, termination="user_stop"):
        async with self._session_stop_lock:
            if not self._session.active and not self._session.finalizing:
                return self._session.last_file

            self._session_stopping = True
            try:
                result = await self.hass.async_add_executor_job(
                    self._session.stop,
                    self._session_summary(),
                    termination,
                )
                return result
            except Exception as err:
                _LOGGER.exception("Unable to finalize simulation session")
                return None
            finally:
                self._session_stopping = False

    async def async_shutdown(self):
        self._control_mode = CONTROL_MODE_SIMULATION
        self._automation_enabled_runtime = False
        await self.async_stop_simulation_session("home_assistant_reload")

    @property
    def control_mode(self):
        return self._control_mode

    async def async_set_control_mode(self, mode: str):
        if mode not in CONTROL_MODE_OPTIONS:
            raise ValueError(f"Unsupported control mode: {mode}")
        # No Live mode and no real-write path exist in v0.6.0.
        self._control_mode = mode
        await self.async_request_refresh()

    def _source_age_seconds(self, entity_id):
        """Return source report age for diagnostics.

        Home Assistant's last_reported is preferred because it can advance even
        when the state value itself does not change. Older HA versions fall back
        to last_updated.
        """
        if not entity_id:
            return 999999.0
        state = self._state(entity_id)
        if state is None:
            return 999999.0
        timestamp = getattr(state, "last_reported", None) or getattr(state, "last_updated", None)
        if timestamp is None:
            return 999999.0
        now = datetime.now(timezone.utc)
        return max(0.0, (now - timestamp).total_seconds())

    def _source_numeric_available(self, entity_id, minimum=None, maximum=None):
        state = self._state(entity_id)
        if not state or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE, "", None):
            return False
        try:
            value = float(state.state)
        except (TypeError, ValueError):
            return False
        if minimum is not None and value < minimum:
            return False
        if maximum is not None and value > maximum:
            return False
        return True

    def list_reports(self):
        return self._session.list_reports()

    @property
    def selected_report(self):
        return self._selected_report

    def set_selected_report(self, filename):
        if filename in self.list_reports():
            self._selected_report = filename

    async def async_prepare_selected_report(self):
        filename = self._selected_report
        if not filename:
            reports = self.list_reports()
            filename = reports[0] if reports else None
        if not filename:
            return None
        source = Path(self.hass.config.path("carpiquet_ems/simulations")) / filename
        target_dir = Path(self.hass.config.path("www/carpiquet_ems_reports"))
        await self.hass.async_add_executor_job(
            lambda: target_dir.mkdir(parents=True, exist_ok=True)
        )
        target = target_dir / filename
        await self.hass.async_add_executor_job(shutil.copy2, source, target)
        self._report_download_url = f"/local/carpiquet_ems_reports/{filename}"
        return self._report_download_url

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
            hyper_real_output = self._state_float(self.config[CONF_HYPER_REAL_OUTPUT_ENTITY])
            solar_real_output = self._state_float(self.config[CONF_SOLARFLOW_REAL_OUTPUT_ENTITY])
            real_zendure_total = max(0.0, hyper_real_output) + max(0.0, solar_real_output)
            hyper_grid_input = self._state_float(
                self.config.get(CONF_HYPER_GRID_INPUT_ENTITY, DEFAULT_HYPER_GRID_INPUT_ENTITY)
            )
            solar_grid_input = self._state_float(
                self.config.get(CONF_SOLARFLOW_GRID_INPUT_ENTITY, DEFAULT_SOLARFLOW_GRID_INPUT_ENTITY)
            )
            # Exact reconstructed house load:
            # Shelly + inverter outputs to house - inverter AC grid inputs.
            house_load_raw = (
                grid
                + real_zendure_total
                - max(0.0, hyper_grid_input)
                - max(0.0, solar_grid_input)
            )
            # Guardrail against asynchronous sensor updates producing an impossible negative load.
            house_load = max(0.0, house_load_raw)

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

            # Session watchdog: runtime engine ON <=> active recorder.
            if self.automation_enabled and not self._session.active:
                await self.async_start_simulation_session()
            elif not self.automation_enabled and self._session.active:
                await self.async_stop_simulation_session("runtime_reconcile")

            now = datetime.now(timezone.utc)
            elapsed = (now - self._automation_last_transition_dt).total_seconds()
            automation_enabled = self.automation_enabled
            allow_fallback = bool(
                self.config.get(CONF_AUTOMATION_ALLOW_FALLBACK, DEFAULT_AUTOMATION_ALLOW_FALLBACK)
            )
            minimum_hold = float(
                self.config.get(
                    CONF_AUTOMATION_MIN_HOLD_SECONDS,
                    DEFAULT_AUTOMATION_MIN_HOLD_SECONDS,
                )
            )
            automation = decide_automation(
                AutomationInput(
                    enabled=automation_enabled,
                    grid_available=grid_ok,
                    active_batteries=active_batteries,
                    fallback_active=fallback_count > 0,
                    allow_fallback=allow_fallback,
                    grid_power_w=grid,
                    grid_target_w=target,
                    deadband_w=deadband,
                    requested_discharge_w=requested,
                    previous_state=self._automation_state,
                    seconds_since_transition=elapsed,
                    minimum_hold_seconds=minimum_hold,
                )
            )
            if automation.transition:
                self._automation_state = automation.state
                self._automation_last_transition_dt = now
            self._automation_cycle += 1

            # Sprint 5 remains simulation-only: automation gates the simulated request.
            if automation.state != "discharge":
                hyper_power = 0.0
                solar_power = 0.0
                total = 0.0
                self._previous_simulated_power = 0.0

            total_capacity = dynamic["hyper_capacity"] + dynamic["solarflow_capacity"]

            if self._virtual_hyper_energy_kwh is None:
                self._virtual_hyper_energy_kwh = dynamic["hyper_capacity"] * hyper_soc / 100.0
            if self._virtual_solarflow_energy_kwh is None:
                self._virtual_solarflow_energy_kwh = dynamic["solarflow_capacity"] * solar_soc / 100.0

            virtual_hyper_soc = 100.0 * self._virtual_hyper_energy_kwh / max(dynamic["hyper_capacity"], 0.001)
            virtual_solar_soc = 100.0 * self._virtual_solarflow_energy_kwh / max(dynamic["solarflow_capacity"], 0.001)

            cycle_now = datetime.now(timezone.utc)
            if self._last_cycle_dt is None:
                cycle_seconds = float(DEFAULT_SCAN_INTERVAL)
            else:
                cycle_seconds = max(0.1, min(30.0, (cycle_now - self._last_cycle_dt).total_seconds()))
            self._last_cycle_dt = cycle_now

            twin = simulate_cycle(
                TwinInput(
                    house_load_w=house_load,
                    grid_target_w=target,
                    hyper_pv_w=hyper_pv,
                    solarflow_pv_w=solar_pv,
                    hyper=TwinBattery(virtual_hyper_soc, dynamic["hyper_min_soc"], dynamic["hyper_max_soc"],
                                      dynamic["hyper_capacity"], dynamic["hyper_max_power"], dynamic["hyper_max_power"], hyper_ok),
                    solarflow=TwinBattery(virtual_solar_soc, dynamic["solarflow_min_soc"], dynamic["solarflow_max_soc"],
                                          dynamic["solarflow_capacity"], dynamic["solarflow_max_power"], dynamic["solarflow_max_power"], solar_ok),
                    deadband_w=deadband,
                    ramp_limit_w=ramp,
                    cycle_seconds=cycle_seconds,
                    previous_hyper_discharge_w=self._twin_prev_hyper_discharge,
                    previous_solarflow_discharge_w=self._twin_prev_solar_discharge,
                    previous_hyper_charge_w=self._twin_prev_hyper_charge,
                    previous_solarflow_charge_w=self._twin_prev_solar_charge,
                )
            )
            self._twin_prev_hyper_discharge = twin.hyper_battery_discharge_w
            self._twin_prev_solar_discharge = twin.solarflow_battery_discharge_w
            self._twin_prev_hyper_charge = twin.hyper_charge_w
            self._twin_prev_solar_charge = twin.solarflow_charge_w

            # v0.6.1 freshness model:
            # - the grid meter is command-critical and must be fresh;
            # - SOC/PV/output entities must be available and numeric, but a stable
            #   value is not considered stale merely because it has not changed.
            hyper_output_entity = self.config.get(CONF_HYPER_REAL_OUTPUT_ENTITY)
            solar_output_entity = self.config.get(CONF_SOLARFLOW_REAL_OUTPUT_ENTITY)

            grid_source_age = self._source_age_seconds(grid_entity)
            hyper_soc_source_age = self._source_age_seconds(hyper_soc_entity)
            solar_soc_source_age = self._source_age_seconds(solar_soc_entity)
            hyper_pv_source_age = self._source_age_seconds(hyper_pv_entity)
            solar_pv_source_age = self._source_age_seconds(solar_pv_entity)
            hyper_output_source_age = self._source_age_seconds(hyper_output_entity)
            solar_output_source_age = self._source_age_seconds(solar_output_entity)

            grid_source_fresh = (
                grid_ok
                and grid_source_age <= DEFAULT_GRID_SOURCE_MAX_AGE_SECONDS
            )

            # Explicit numeric validation avoids treating unknown/unavailable as 0.
            hyper_command_sources_ok = (
                self._source_numeric_available(hyper_soc_entity, 0.0, 100.0)
                and self._source_numeric_available(hyper_pv_entity, 0.0)
                and self._source_numeric_available(hyper_output_entity, 0.0)
            )
            solar_command_sources_ok = (
                self._source_numeric_available(solar_soc_entity, 0.0, 100.0)
                and self._source_numeric_available(solar_pv_entity, 0.0)
                and self._source_numeric_available(solar_output_entity, 0.0)
            )

            command_request = CommandRequest(
                hyper_output_w=max(0.0, twin.hyper_home_w),
                solarflow_output_w=max(0.0, twin.solarflow_home_w),
            )
            command_decision = evaluate_command(
                self._control_mode,
                command_request,
                SafetyContext(
                    grid_available=grid_ok,
                    grid_fresh=grid_source_fresh,
                    hyper_available=hyper_ok and hyper_command_sources_ok,
                    solarflow_available=solar_ok and solar_command_sources_ok,
                    initialization_ready=self._initialization_ready,
                    fallback_active=fallback_count > 0,
                    allow_fallback=bool(
                        self.config.get(CONF_AUTOMATION_ALLOW_FALLBACK, DEFAULT_AUTOMATION_ALLOW_FALLBACK)
                    ),
                    hyper_soc=hyper_soc,
                    solarflow_soc=solar_soc,
                    hyper_min_soc=dynamic["hyper_min_soc"],
                    solarflow_min_soc=dynamic["solarflow_min_soc"],
                    hyper_pv_w=hyper_pv,
                    solarflow_pv_w=solar_pv,
                    hyper_max_power_w=dynamic["hyper_max_power"],
                    solarflow_max_power_w=dynamic["solarflow_max_power"],
                    grid_source_age_seconds=grid_source_age,
                    grid_max_age_seconds=DEFAULT_GRID_SOURCE_MAX_AGE_SECONDS,
                ),
            )
            self._shadow_cycle += 1
            if command_decision.safety_ok:
                self._shadow_accepted += 1
            else:
                self._shadow_rejected += 1

            actual_hyper_output_limit = self._state_float(
                self.config.get(CONF_HYPER_OUTPUT_ENTITY), default=0.0
            )
            actual_solar_output_limit = self._state_float(
                self.config.get(CONF_SOLARFLOW_OUTPUT_ENTITY), default=0.0
            )

            dt_h = cycle_seconds / 3600.0
            hdelta = (twin.hyper_charge_w - twin.hyper_battery_discharge_w) * dt_h / 1000.0
            sdelta = (twin.solarflow_charge_w - twin.solarflow_battery_discharge_w) * dt_h / 1000.0

            hmin = dynamic["hyper_capacity"] * dynamic["hyper_min_soc"] / 100.0
            hmax = dynamic["hyper_capacity"] * dynamic["hyper_max_soc"] / 100.0
            smin = dynamic["solarflow_capacity"] * dynamic["solarflow_min_soc"] / 100.0
            smax = dynamic["solarflow_capacity"] * dynamic["solarflow_max_soc"] / 100.0

            self._virtual_hyper_energy_kwh = max(hmin, min(hmax, self._virtual_hyper_energy_kwh + hdelta))
            self._virtual_solarflow_energy_kwh = max(smin, min(smax, self._virtual_solarflow_energy_kwh + sdelta))

            virtual_hyper_soc = 100.0 * self._virtual_hyper_energy_kwh / max(dynamic["hyper_capacity"], 0.001)
            virtual_solar_soc = 100.0 * self._virtual_solarflow_energy_kwh / max(dynamic["solarflow_capacity"], 0.001)

            real_grid_error = abs(grid-target)
            sim_grid_error = abs(twin.grid_w-target)
            # Progressive score: full score inside the smoothing range, then gradual decay.
            score_scale = max(100.0, deadband * 5.0)
            def _score(error_w):
                if error_w <= deadband:
                    return 100.0
                return 100.0 / (1.0 + ((error_w - deadband) / score_scale))
            perf_score = _score(sim_grid_error)
            zendure_score = _score(real_grid_error)
            self._perf_samples += 1
            self._perf_score_sum += perf_score
            self._zendure_score_sum += zendure_score
            # Integrate energy using the actual coordinator interval.
            self._real_import_kwh += max(0.0, grid) * dt_h / 1000.0
            self._real_export_kwh += max(0.0, -grid) * dt_h / 1000.0
            self._sim_import_kwh += max(0.0, twin.grid_w) * dt_h / 1000.0
            self._sim_export_kwh += max(0.0, -twin.grid_w) * dt_h / 1000.0
            self._pv_charged_kwh += max(0.0, twin.hyper_charge_w + twin.solarflow_charge_w) * dt_h / 1000.0
            self._pv_curtailed_kwh += max(0.0, twin.curtailed_pv_w) * dt_h / 1000.0
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
            status = "Sain" if health == 100 else "Attention" if health >= 67 else "Critique"

            result_data = {
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
                ATTR_DATA_MODE: "DIRECT" if fallback_count == 0 else "SECOURS ACTIF",
                ATTR_FALLBACK_ACTIVE_COUNT: fallback_count,
                ATTR_LAST_FALLBACK_SYNC: self._last_fallback_sync or "Jamais",
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
                ATTR_AUTOMATION_STATE: DISPLAY_STATE.get(automation.state, automation.state),
                ATTR_AUTOMATION_REASON: DISPLAY_REASON.get(automation.reason, automation.reason),
                ATTR_AUTOMATION_REQUEST_W: automation.request_w,
                ATTR_AUTOMATION_CYCLE: self._automation_cycle,
                ATTR_AUTOMATION_LAST_TRANSITION: self._automation_last_transition_dt.isoformat(),
                ATTR_AUTOMATION_HOLD_REMAINING: automation.hold_remaining_seconds,
                ATTR_AUTOMATION_SAFETY_OK: automation.safety_ok,
                ATTR_AUTOMATION_POLICY: POLICY,
                ATTR_AUTOMATION_ENABLED: automation_enabled,
                ATTR_HOUSE_LOAD: round(house_load,1),
                ATTR_HOUSE_LOAD_RAW: round(house_load_raw,1),
                ATTR_REAL_ZENDURE_TOTAL_OUTPUT: round(real_zendure_total,1),
                ATTR_REAL_HYPER_OUTPUT: round(hyper_real_output,1),
                ATTR_REAL_SOLARFLOW_OUTPUT: round(solar_real_output,1),
                ATTR_REAL_HYPER_GRID_INPUT: round(hyper_grid_input,1),
                ATTR_REAL_SOLARFLOW_GRID_INPUT: round(solar_grid_input,1),
                ATTR_SIM_HYPER_HOME: twin.hyper_home_w,
                ATTR_HYPER_PV_TO_HOME: twin.hyper_pv_to_home_w,
                ATTR_HYPER_BATTERY_DISCHARGE: twin.hyper_battery_discharge_w,
                ATTR_SIM_SOLARFLOW_HOME: twin.solarflow_home_w,
                ATTR_SOLARFLOW_PV_TO_HOME: twin.solarflow_pv_to_home_w,
                ATTR_SOLARFLOW_BATTERY_DISCHARGE: twin.solarflow_battery_discharge_w,
                ATTR_SIM_HYPER_CHARGE: twin.hyper_charge_w,
                ATTR_SIM_SOLARFLOW_CHARGE: twin.solarflow_charge_w,
                ATTR_SIM_HYPER_EXPORT_POOL: twin.hyper_export_pool_w,
                ATTR_SIM_SOLARFLOW_EXPORT_POOL: twin.solarflow_export_pool_w,
                ATTR_SIM_CROSS_CHARGE_HYPER: twin.cross_charge_hyper_w,
                ATTR_SIM_CROSS_CHARGE_SOLARFLOW: twin.cross_charge_solarflow_w,
                ATTR_SIM_GRID_FINAL: twin.grid_w,
                ATTR_REAL_GRID_ERROR: round(real_grid_error,1),
                ATTR_SIM_GRID_ERROR: round(sim_grid_error,1),
                ATTR_PERFORMANCE_SCORE: round(perf_score,1),
                ATTR_ZENDURE_REFERENCE_SCORE: round(zendure_score,1),
                ATTR_PERFORMANCE_GAIN: round(perf_score-zendure_score,1),
                ATTR_VIRTUAL_HYPER_ENERGY: round(self._virtual_hyper_energy_kwh,4),
                ATTR_VIRTUAL_SOLARFLOW_ENERGY: round(self._virtual_solarflow_energy_kwh,4),
                ATTR_VIRTUAL_HYPER_SOC: round(virtual_hyper_soc,1),
                ATTR_VIRTUAL_SOLARFLOW_SOC: round(virtual_solar_soc,1),
                ATTR_PV_TOTAL: round(hyper_pv+solar_pv,1),
                ATTR_SOLAR_SURPLUS: twin.surplus_w,
                ATTR_PV_CURTAILED: twin.curtailed_pv_w,
                ATTR_GRID_EXPORT_ALLOWED: twin.grid_export_allowed,
                ATTR_GRID_EXPORT_BLOCK_REASON: twin.grid_export_block_reason,
                ATTR_FULL_SYSTEMS_COUNT: twin.full_systems_count,
                ATTR_OPERATION_MODE: twin.mode,
                ATTR_PERF_SAMPLE_COUNT: self._perf_samples,
                ATTR_PERFORMANCE_AVERAGE: round(self._perf_score_sum / self._perf_samples, 1) if self._perf_samples else 0.0,
                ATTR_ZENDURE_AVERAGE: round(self._zendure_score_sum / self._perf_samples, 1) if self._perf_samples else 0.0,
                ATTR_REAL_IMPORT_ENERGY: round(self._real_import_kwh, 4),
                ATTR_REAL_EXPORT_ENERGY: round(self._real_export_kwh, 4),
                ATTR_SIM_IMPORT_ENERGY: round(self._sim_import_kwh, 4),
                ATTR_SIM_EXPORT_ENERGY: round(self._sim_export_kwh, 4),
                ATTR_PV_CHARGED_ENERGY: round(self._pv_charged_kwh, 4),
                ATTR_PV_CURTAILED_ENERGY: round(self._pv_curtailed_kwh, 4),
                ATTR_CONTROL_MODE: self._control_mode,
                ATTR_COMMAND_PIPELINE_STATE: (
                    "Shadow actif" if self._control_mode == CONTROL_MODE_SHADOW
                    else "Armed verrouillé" if self._control_mode == CONTROL_MODE_ARMED
                    else "Simulation"
                ),
                ATTR_COMMAND_WRITE_LOCKED: command_decision.write_locked,
                ATTR_COMMAND_SAFETY_OK: command_decision.safety_ok,
                ATTR_COMMAND_SAFETY_LIMITED: command_decision.safety_limited,
                ATTR_COMMAND_SAFETY_REASON: command_decision.safety_reason,
                ATTR_WOULD_SEND_COMMAND: command_decision.would_send_command,
                ATTR_REQUESTED_HYPER_OUTPUT: round(command_decision.requested.hyper_output_w, 1),
                ATTR_VALIDATED_HYPER_OUTPUT: round(command_decision.validated.hyper_output_w, 1),
                ATTR_REQUESTED_SOLARFLOW_OUTPUT: round(command_decision.requested.solarflow_output_w, 1),
                ATTR_VALIDATED_SOLARFLOW_OUTPUT: round(command_decision.validated.solarflow_output_w, 1),
                ATTR_ACTUAL_HYPER_OUTPUT_LIMIT: round(actual_hyper_output_limit, 1),
                ATTR_ACTUAL_SOLARFLOW_OUTPUT_LIMIT: round(actual_solar_output_limit, 1),
                ATTR_HYPER_COMMAND_DELTA: round(command_decision.validated.hyper_output_w - actual_hyper_output_limit, 1),
                ATTR_SOLARFLOW_COMMAND_DELTA: round(command_decision.validated.solarflow_output_w - actual_solar_output_limit, 1),
                ATTR_COMMAND_EVALUATION_AT: command_decision.evaluated_at,
                ATTR_COMMAND_WATCHDOG_STATE: command_decision.watchdog_state,
                ATTR_COMMAND_SOURCE_AGE: round(grid_source_age, 1),
                ATTR_GRID_SOURCE_AGE: round(grid_source_age, 1),
                ATTR_HYPER_SOC_SOURCE_AGE: round(hyper_soc_source_age, 1),
                ATTR_SOLARFLOW_SOC_SOURCE_AGE: round(solar_soc_source_age, 1),
                ATTR_HYPER_PV_SOURCE_AGE: round(hyper_pv_source_age, 1),
                ATTR_SOLARFLOW_PV_SOURCE_AGE: round(solar_pv_source_age, 1),
                ATTR_HYPER_OUTPUT_SOURCE_AGE: round(hyper_output_source_age, 1),
                ATTR_SOLARFLOW_OUTPUT_SOURCE_AGE: round(solar_output_source_age, 1),
                ATTR_GRID_SOURCE_FRESH: grid_source_fresh,
                ATTR_SOURCE_FRESHNESS_MODEL: "grid_strict_other_sources_availability",
                ATTR_SHADOW_CYCLE: self._shadow_cycle,
                ATTR_SHADOW_ACCEPTED: self._shadow_accepted,
                ATTR_SHADOW_REJECTED: self._shadow_rejected,
                ATTR_SESSION_ID: self._session.session_id or "Aucune",
                ATTR_SESSION_ACTIVE: self._session.active,
                ATTR_SESSION_STARTED_AT: self._session.started_at.isoformat() if self._session.started_at else "Jamais",
                ATTR_SESSION_DURATION: round((datetime.now(timezone.utc)-self._session.started_at).total_seconds(),1) if self._session.started_at else 0.0,
                ATTR_SESSION_SAMPLE_COUNT: self._session.sample_count,
                ATTR_LAST_SESSION_FILE: self._session.last_file or "Aucun",
                ATTR_SESSION_RECORDING_STATE: self._session.recording_state,
                ATTR_SESSION_FINALIZING: self._session.finalizing or self._session_stopping,
                ATTR_SESSION_SAVE_ERROR: self._session.last_error or "Aucune",
                ATTR_LAST_SESSION_ENDED_AT: self._session.last_ended_at or "Jamais",
                ATTR_ENGINE_INITIALIZATION_STATE: self._initialization_state,
                ATTR_ENGINE_INITIALIZATION_ERROR: self._initialization_error or "Aucune",
                ATTR_ENGINE_INITIALIZATION_READY: self._initialization_ready,
                ATTR_SELECTED_REPORT: self._selected_report or "Aucun",
                ATTR_REPORT_DOWNLOAD_URL: self._report_download_url or "Aucun",
                ATTR_DYNAMIC_SOURCES: sources,
                ATTR_FALLBACKS: dict(self._fallbacks),
            }
            session_sample = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "grid_real_w": result_data.get(ATTR_GRID_POWER),
                "house_load_w": result_data.get(ATTR_HOUSE_LOAD),
                "house_load_raw_w": result_data.get(ATTR_HOUSE_LOAD_RAW),
                "cycle_seconds": cycle_seconds,
                "hyper_pv_w": result_data.get(ATTR_HYPER_PV),
                "solarflow_pv_w": result_data.get(ATTR_SOLARFLOW_PV),
                "hyper_real_output_w": result_data.get(ATTR_REAL_HYPER_OUTPUT),
                "solarflow_real_output_w": result_data.get(ATTR_REAL_SOLARFLOW_OUTPUT),
                "hyper_grid_input_w": result_data.get(ATTR_REAL_HYPER_GRID_INPUT),
                "solarflow_grid_input_w": result_data.get(ATTR_REAL_SOLARFLOW_GRID_INPUT),
                "hyper_simulated_home_w": result_data.get(ATTR_SIM_HYPER_HOME),
                "hyper_pv_to_home_w": result_data.get(ATTR_HYPER_PV_TO_HOME),
                "hyper_battery_discharge_w": result_data.get(ATTR_HYPER_BATTERY_DISCHARGE),
                "solarflow_simulated_home_w": result_data.get(ATTR_SIM_SOLARFLOW_HOME),
                "solarflow_pv_to_home_w": result_data.get(ATTR_SOLARFLOW_PV_TO_HOME),
                "solarflow_battery_discharge_w": result_data.get(ATTR_SOLARFLOW_BATTERY_DISCHARGE),
                "hyper_simulated_charge_w": result_data.get(ATTR_SIM_HYPER_CHARGE),
                "solarflow_simulated_charge_w": result_data.get(ATTR_SIM_SOLARFLOW_CHARGE),
                "grid_simulated_w": result_data.get(ATTR_SIM_GRID_FINAL),
                "virtual_hyper_soc_percent": result_data.get(ATTR_VIRTUAL_HYPER_SOC),
                "virtual_solarflow_soc_percent": result_data.get(ATTR_VIRTUAL_SOLARFLOW_SOC),
                "performance_score_percent": result_data.get(ATTR_PERFORMANCE_SCORE),
                "performance_average_percent": result_data.get(ATTR_PERFORMANCE_AVERAGE),
                "zendure_reference_score_percent": result_data.get(ATTR_ZENDURE_REFERENCE_SCORE),
                "operation_mode": result_data.get(ATTR_OPERATION_MODE),
                "pv_curtailed_w": result_data.get(ATTR_PV_CURTAILED),
                "grid_export_allowed": result_data.get(ATTR_GRID_EXPORT_ALLOWED),
                "grid_export_block_reason": result_data.get(ATTR_GRID_EXPORT_BLOCK_REASON),
                "full_systems_count": result_data.get(ATTR_FULL_SYSTEMS_COUNT),
                "control_mode": result_data.get(ATTR_CONTROL_MODE),
                "command_pipeline_state": result_data.get(ATTR_COMMAND_PIPELINE_STATE),
                "command_safety_ok": result_data.get(ATTR_COMMAND_SAFETY_OK),
                "command_safety_limited": result_data.get(ATTR_COMMAND_SAFETY_LIMITED),
                "command_safety_reason": result_data.get(ATTR_COMMAND_SAFETY_REASON),
                "would_send_command": result_data.get(ATTR_WOULD_SEND_COMMAND),
                "requested_hyper_output_w": result_data.get(ATTR_REQUESTED_HYPER_OUTPUT),
                "validated_hyper_output_w": result_data.get(ATTR_VALIDATED_HYPER_OUTPUT),
                "requested_solarflow_output_w": result_data.get(ATTR_REQUESTED_SOLARFLOW_OUTPUT),
                "validated_solarflow_output_w": result_data.get(ATTR_VALIDATED_SOLARFLOW_OUTPUT),
                "actual_hyper_output_limit_w": result_data.get(ATTR_ACTUAL_HYPER_OUTPUT_LIMIT),
                "actual_solarflow_output_limit_w": result_data.get(ATTR_ACTUAL_SOLARFLOW_OUTPUT_LIMIT),
                "hyper_command_delta_w": result_data.get(ATTR_HYPER_COMMAND_DELTA),
                "solarflow_command_delta_w": result_data.get(ATTR_SOLARFLOW_COMMAND_DELTA),
                "command_source_age_seconds": result_data.get(ATTR_COMMAND_SOURCE_AGE),
                "command_watchdog_state": result_data.get(ATTR_COMMAND_WATCHDOG_STATE),
                "grid_source_age_seconds": result_data.get(ATTR_GRID_SOURCE_AGE),
                "hyper_soc_source_age_seconds": result_data.get(ATTR_HYPER_SOC_SOURCE_AGE),
                "solarflow_soc_source_age_seconds": result_data.get(ATTR_SOLARFLOW_SOC_SOURCE_AGE),
                "hyper_pv_source_age_seconds": result_data.get(ATTR_HYPER_PV_SOURCE_AGE),
                "solarflow_pv_source_age_seconds": result_data.get(ATTR_SOLARFLOW_PV_SOURCE_AGE),
                "hyper_output_source_age_seconds": result_data.get(ATTR_HYPER_OUTPUT_SOURCE_AGE),
                "solarflow_output_source_age_seconds": result_data.get(ATTR_SOLARFLOW_OUTPUT_SOURCE_AGE),
                "grid_source_fresh": result_data.get(ATTR_GRID_SOURCE_FRESH),
                "source_freshness_model": result_data.get(ATTR_SOURCE_FRESHNESS_MODEL),
            }
            if self._automation_enabled_runtime and not self._session_stopping:
                self._session.append(session_sample)
            result_data[ATTR_SESSION_SAMPLE_COUNT] = self._session.sample_count
            return result_data
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Unable to calculate EMS state: {err}") from err
