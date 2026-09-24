from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import (
    DOMAIN, CONTROL_MODE_OPTIONS,
    TRANSPORT_HYPER_OPTIONS, TRANSPORT_SOLARFLOW_OPTIONS,
    ATTR_TRANSPORT_HYPER_SELECTED, ATTR_TRANSPORT_HYPER_FALLBACK_REASON,
    ATTR_TRANSPORT_SOLARFLOW_SELECTED, ATTR_TRANSPORT_SOLARFLOW_FALLBACK_REASON,
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SimulationReportSelect(coordinator, entry), ControlModeSelect(coordinator, entry), ControlledTestDeviceSelect(coordinator, entry)]
    profiles = {
        str(system.get("control_profile") or "")
        for system in coordinator._zendure_discovery.get("systems", [])
    }
    if "legacy_hyper" in profiles:
        entities.append(HyperTransportSelect(coordinator, entry))
    if "zensdk_ac" in profiles:
        entities.append(SolarFlowTransportSelect(coordinator, entry))
    async_add_entities(entities)

class SimulationReportSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Simulation Report"
        self._attr_unique_id = f"{entry.entry_id}_simulation_report"
        self._attr_icon = "mdi:file-chart-outline"

    @property
    def options(self):
        reports = self.coordinator.list_reports()
        return reports or ["Aucun rapport"]

    @property
    def current_option(self):
        selected = self.coordinator.selected_report
        return selected if selected in self.options else self.options[0]

    async def async_select_option(self, option):
        if option != "Aucun rapport":
            self.coordinator.set_selected_report(option)
        self.async_write_ha_state()


class ControlModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Control Mode"
        self._attr_unique_id = f"{entry.entry_id}_control_mode"
        self._attr_icon = "mdi:shield-lock-outline"
        self._attr_options = list(CONTROL_MODE_OPTIONS)

    @property
    def current_option(self):
        return self.coordinator.control_mode

    async def async_select_option(self, option):
        await self.coordinator.async_set_control_mode(option)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {
            "real_writes_enabled": False,
            "restart_default": "Simulation",
            "safety_note": "v0.6.4-alpha-sprint6 never writes to Zendure",
        }


class HyperTransportSelect(CoordinatorEntity, SelectEntity):
    """Select Hyper transport policy without enabling execution."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Hyper Transport"
        self._attr_unique_id = f"{entry.entry_id}_hyper_transport"
        self._attr_icon = "mdi:lan-connect"
        self._attr_options = list(TRANSPORT_HYPER_OPTIONS)

    @property
    def current_option(self):
        return self.coordinator.hyper_transport_selection

    async def async_select_option(self, option):
        await self.coordinator.async_set_hyper_transport_selection(option)

    @property
    def extra_state_attributes(self):
        diag = self.coordinator._transport_policy_diagnostics()
        return {
            "selected_transport": diag[ATTR_TRANSPORT_HYPER_SELECTED],
            "selection_reason": diag[ATTR_TRANSPORT_HYPER_FALLBACK_REASON],
            "execution_enabled": False,
            "write_locked": True,
        }


class SolarFlowTransportSelect(CoordinatorEntity, SelectEntity):
    """Select SolarFlow transport policy without enabling execution."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS SolarFlow Transport"
        self._attr_unique_id = f"{entry.entry_id}_solarflow_transport"
        self._attr_icon = "mdi:lan-connect"
        self._attr_options = list(TRANSPORT_SOLARFLOW_OPTIONS)

    @property
    def current_option(self):
        return self.coordinator.solarflow_transport_selection

    async def async_select_option(self, option):
        await self.coordinator.async_set_solarflow_transport_selection(option)

    @property
    def extra_state_attributes(self):
        diag = self.coordinator._transport_policy_diagnostics()
        return {
            "selected_transport": diag[ATTR_TRANSPORT_SOLARFLOW_SELECTED],
            "selection_reason": diag[ATTR_TRANSPORT_SOLARFLOW_FALLBACK_REASON],
            "local_http_qualified": bool(
                self.coordinator._solarflow_local_probe
                and self.coordinator._solarflow_local_probe.qualified
            ),
            "execution_enabled": False,
            "write_locked": True,
        }


class ControlledTestDeviceSelect(CoordinatorEntity, SelectEntity):
    """Select one test target. Changing target always disarms the gate."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Controlled Test Device"
        self._attr_unique_id = f"{entry.entry_id}_controlled_test_device"
        self._attr_icon = "mdi:target"
        self._attr_options = ["Aucun", "Hyper 2000", "SolarFlow 2400 Pro"]

    @property
    def current_option(self):
        return {
            "hyper": "Hyper 2000",
            "solarflow": "SolarFlow 2400 Pro",
        }.get(self.coordinator.test_gate_device, "Aucun")

    async def async_select_option(self, option):
        device = {
            "Aucun": "",
            "Hyper 2000": "hyper",
            "SolarFlow 2400 Pro": "solarflow",
        }[option]
        await self.coordinator.async_set_test_gate_device(device)
