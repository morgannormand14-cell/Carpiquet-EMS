from __future__ import annotations

from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import *
from .zendure_discovery import discover_zendure_inventory


def _entity(domain: str):
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain, multiple=False))

GRID_SCHEMA = vol.Schema({vol.Required(CONF_GRID_POWER_ENTITY): _entity("sensor")})
CONFIRM_SCHEMA = vol.Schema({vol.Required("confirm_inventory", default=True): bool})


def _system_by_profile(snapshot, profile):
    return next((s for s in snapshot.get("systems", []) if s.get("control_profile") == profile), None)

def _entity(system, key):
    return (system or {}).get("entities", {}).get(key)

def _legacy_data_from_discovery(grid_entity: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Bridge Step 2B discovery to the frozen two-system legacy engine.

    This does not give Discovery authority. It only supplies the entity IDs the
    validated v0.6.4 engine already consumes until the generic engine cutover.
    """
    hyper=_system_by_profile(snapshot, "legacy_hyper")
    solar=_system_by_profile(snapshot, "zensdk_ac")
    if hyper is None or solar is None:
        raise ValueError("required_current_systems_not_detected")
    required={
      CONF_GRID_POWER_ENTITY:grid_entity,
      CONF_HYPER_SOC_ENTITY:_entity(hyper,"soc"), CONF_HYPER_PV_ENTITY:_entity(hyper,"pv_w"),
      CONF_HYPER_OUTPUT_ENTITY:_entity(hyper,"command_limit_w"), CONF_HYPER_REAL_OUTPUT_ENTITY:_entity(hyper,"home_output_w"),
      CONF_HYPER_GRID_INPUT_ENTITY:_entity(hyper,"grid_input_w"), CONF_HYPER_CAPACITY_ENTITY:_entity(hyper,"capacity_kwh"),
      CONF_HYPER_MAX_POWER_ENTITY:_entity(hyper,"max_discharge_w"), CONF_HYPER_MIN_SOC_ENTITY:_entity(hyper,"min_soc"), CONF_HYPER_MAX_SOC_ENTITY:_entity(hyper,"max_soc"),
      CONF_SOLARFLOW_SOC_ENTITY:_entity(solar,"soc"), CONF_SOLARFLOW_PV_ENTITY:_entity(solar,"pv_w"),
      CONF_SOLARFLOW_OUTPUT_ENTITY:_entity(solar,"command_limit_w"), CONF_SOLARFLOW_REAL_OUTPUT_ENTITY:_entity(solar,"home_output_w"),
      CONF_SOLARFLOW_GRID_INPUT_ENTITY:_entity(solar,"grid_input_w"), CONF_SOLARFLOW_CAPACITY_ENTITY:_entity(solar,"capacity_kwh"),
      CONF_SOLARFLOW_MAX_POWER_ENTITY:_entity(solar,"max_discharge_w"), CONF_SOLARFLOW_MIN_SOC_ENTITY:_entity(solar,"min_soc"), CONF_SOLARFLOW_MAX_SOC_ENTITY:_entity(solar,"max_soc"),
    }
    missing=[k for k,v in required.items() if not v]
    if missing: raise ValueError("missing_required_entities:"+",".join(missing))
    required.update({
      CONF_GRID_TARGET:DEFAULT_GRID_TARGET, CONF_GRID_DEADBAND:DEFAULT_GRID_DEADBAND, CONF_RAMP_LIMIT_W:DEFAULT_RAMP_LIMIT_W,
      CONF_AUTOMATION_ENABLED:DEFAULT_AUTOMATION_ENABLED, CONF_AUTOMATION_MIN_HOLD_SECONDS:DEFAULT_AUTOMATION_MIN_HOLD_SECONDS,
      CONF_AUTOMATION_ALLOW_FALLBACK:DEFAULT_AUTOMATION_ALLOW_FALLBACK, CONF_BATTERIES:[],
      "zendure_inventory":snapshot,
    })
    # Seed the frozen engine fallbacks from live discovered entities.
    fallback_map=((CONF_HYPER_CAPACITY_ENTITY,CONF_FALLBACK_HYPER_CAPACITY),(CONF_SOLARFLOW_CAPACITY_ENTITY,CONF_FALLBACK_SOLARFLOW_CAPACITY),
      (CONF_HYPER_MAX_POWER_ENTITY,CONF_FALLBACK_HYPER_MAX_POWER),(CONF_SOLARFLOW_MAX_POWER_ENTITY,CONF_FALLBACK_SOLARFLOW_MAX_POWER),
      (CONF_HYPER_MIN_SOC_ENTITY,CONF_FALLBACK_HYPER_MIN_SOC),(CONF_HYPER_MAX_SOC_ENTITY,CONF_FALLBACK_HYPER_MAX_SOC),
      (CONF_SOLARFLOW_MIN_SOC_ENTITY,CONF_FALLBACK_SOLARFLOW_MIN_SOC),(CONF_SOLARFLOW_MAX_SOC_ENTITY,CONF_FALLBACK_SOLARFLOW_MAX_SOC))
    for entity_key,fallback_key in fallback_map:
        st = None
        # actual state is seeded by caller after discovery; zero is never used silently
        required[fallback_key] = None
    return required

class CarpiquetEMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION=4
    def __init__(self):
        self._grid_entity=None; self._snapshot=None

    async def async_step_user(self,user_input=None)->FlowResult:
        await self.async_set_unique_id(DOMAIN); self._abort_if_unique_id_configured()
        if user_input is not None:
            self._grid_entity=user_input[CONF_GRID_POWER_ENTITY]
            self._snapshot=discover_zendure_inventory(self.hass)
            if self._snapshot.get("systems_count",0) < 1:
                return self.async_show_form(step_id="user",data_schema=GRID_SCHEMA,errors={"base":"no_zendure_system"})
            return await self.async_step_inventory()
        return self.async_show_form(step_id="user",data_schema=GRID_SCHEMA)

    async def async_step_inventory(self,user_input=None)->FlowResult:
        snap=self._snapshot or {}
        systems=snap.get("systems",[])
        summary="\n\n".join(
            "\n".join(
                [
                    f"**{s.get('name')} ({s.get('model')})** — {len(s.get('batteries', []))} batterie(s)",
                    *[
                        f"• {b.get('name')} ({b.get('model')})"
                        for b in s.get("batteries", [])
                    ],
                ]
            )
            for s in systems
        )
        infrastructure="\n".join(
            f"• {row.get('name') or row.get('model') or row.get('device_id')}"
            for row in snap.get("infrastructure", [])
        ) or "Aucune"
        if user_input is not None:
            if not user_input.get("confirm_inventory"):
                return self.async_abort(reason="inventory_rejected")
            try:
                data=_legacy_data_from_discovery(self._grid_entity,snap)
                # Seed numeric fallbacks from HA now, refusing incomplete telemetry.
                pairs=((CONF_HYPER_CAPACITY_ENTITY,CONF_FALLBACK_HYPER_CAPACITY),(CONF_SOLARFLOW_CAPACITY_ENTITY,CONF_FALLBACK_SOLARFLOW_CAPACITY),
                  (CONF_HYPER_MAX_POWER_ENTITY,CONF_FALLBACK_HYPER_MAX_POWER),(CONF_SOLARFLOW_MAX_POWER_ENTITY,CONF_FALLBACK_SOLARFLOW_MAX_POWER),
                  (CONF_HYPER_MIN_SOC_ENTITY,CONF_FALLBACK_HYPER_MIN_SOC),(CONF_HYPER_MAX_SOC_ENTITY,CONF_FALLBACK_HYPER_MAX_SOC),
                  (CONF_SOLARFLOW_MIN_SOC_ENTITY,CONF_FALLBACK_SOLARFLOW_MIN_SOC),(CONF_SOLARFLOW_MAX_SOC_ENTITY,CONF_FALLBACK_SOLARFLOW_MAX_SOC))
                for ek,fk in pairs:
                    st=self.hass.states.get(data[ek]); data[fk]=float(st.state) if st and st.state not in ("unknown","unavailable") else None
                if any(data[fk] is None for _,fk in pairs): raise ValueError("dynamic_value_unavailable")
            except Exception:
                return self.async_show_form(step_id="inventory",data_schema=CONFIRM_SCHEMA,errors={"base":"discovery_mapping_incomplete"},description_placeholders={"systems":str(snap.get("systems_count",0)),"batteries":str(snap.get("batteries_count",0)),"summary":summary,"infrastructure":infrastructure})
            return self.async_create_entry(title="Carpiquet EMS",data=data)
        return self.async_show_form(step_id="inventory",data_schema=CONFIRM_SCHEMA,description_placeholders={"systems":str(snap.get("systems_count",0)),"batteries":str(snap.get("batteries_count",0)),"summary":summary,"infrastructure":infrastructure})

    @staticmethod
    def async_get_options_flow(config_entry):
        return CarpiquetEMSOptionsFlow(config_entry)

class CarpiquetEMSOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    def _pending(self):
        coordinator = self.hass.data.get(DOMAIN, {}).get(self._config_entry.entry_id)
        if coordinator is None:
            return None, None, None
        pending, comparison = coordinator.get_pending_zendure_reconciliation()
        return coordinator, pending, comparison

    async def async_step_init(self, user_input=None) -> FlowResult:
        coordinator, pending, comparison = self._pending()
        if pending is not None and comparison is not None:
            return await self.async_step_reconcile()
        current = self._config_entry.options.get(
            CONF_GRID_POWER_ENTITY, self._config_entry.data.get(CONF_GRID_POWER_ENTITY)
        )
        schema = vol.Schema({vol.Required(CONF_GRID_POWER_ENTITY, default=current): _entity("sensor")})
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_reconcile(self, user_input=None) -> FlowResult:
        coordinator, pending, comparison = self._pending()
        if pending is None or comparison is None:
            return self.async_abort(reason="no_pending_reconciliation")
        systems = pending.get("systems", [])
        summary = " | ".join(
            f"{row.get('name')} ({row.get('model')}) — {len(row.get('batteries', []))} batterie(s)"
            for row in systems
        )
        changes = (
            f"Ajoutés: {len(comparison.get('added_system_ids', []))} — "
            f"Modifiés: {len(comparison.get('changed_system_ids', []))} — "
            f"Absents lors de ce scan: {len(comparison.get('missing_system_ids', []))}"
        )
        return self.async_show_menu(
            step_id="reconcile",
            menu_options=["apply", "reject"],
            description_placeholders={
                "systems": str(pending.get("systems_count", 0)),
                "batteries": str(pending.get("batteries_count", 0)),
                "summary": summary or "Aucun système",
                "changes": changes,
            },
        )

    async def async_step_apply(self, user_input=None) -> FlowResult:
        coordinator, pending, comparison = self._pending()
        if pending is None:
            return self.async_abort(reason="no_pending_reconciliation")
        try:
            grid = self._config_entry.options.get(
                CONF_GRID_POWER_ENTITY, self._config_entry.data.get(CONF_GRID_POWER_ENTITY)
            )
            data = _legacy_data_from_discovery(grid, pending)
            pairs = (
                (CONF_HYPER_CAPACITY_ENTITY, CONF_FALLBACK_HYPER_CAPACITY),
                (CONF_SOLARFLOW_CAPACITY_ENTITY, CONF_FALLBACK_SOLARFLOW_CAPACITY),
                (CONF_HYPER_MAX_POWER_ENTITY, CONF_FALLBACK_HYPER_MAX_POWER),
                (CONF_SOLARFLOW_MAX_POWER_ENTITY, CONF_FALLBACK_SOLARFLOW_MAX_POWER),
                (CONF_HYPER_MIN_SOC_ENTITY, CONF_FALLBACK_HYPER_MIN_SOC),
                (CONF_HYPER_MAX_SOC_ENTITY, CONF_FALLBACK_HYPER_MAX_SOC),
                (CONF_SOLARFLOW_MIN_SOC_ENTITY, CONF_FALLBACK_SOLARFLOW_MIN_SOC),
                (CONF_SOLARFLOW_MAX_SOC_ENTITY, CONF_FALLBACK_SOLARFLOW_MAX_SOC),
            )
            for entity_key, fallback_key in pairs:
                st = self.hass.states.get(data[entity_key])
                data[fallback_key] = float(st.state) if st and st.state not in ("unknown", "unavailable") else None
            if any(data[fallback_key] is None for _, fallback_key in pairs):
                raise ValueError("dynamic_value_unavailable")
        except Exception:
            return self.async_abort(reason="reconciliation_mapping_incomplete")
        coordinator.clear_pending_zendure_reconciliation()
        self.hass.config_entries.async_update_entry(self._config_entry, data=data)
        return self.async_create_entry(title="", data=dict(self._config_entry.options))

    async def async_step_reject(self, user_input=None) -> FlowResult:
        coordinator, pending, comparison = self._pending()
        if coordinator is not None:
            coordinator.clear_pending_zendure_reconciliation()
        return self.async_create_entry(title="", data=dict(self._config_entry.options))
