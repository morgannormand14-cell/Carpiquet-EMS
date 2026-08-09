from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONTROL_MODE_OPTIONS

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SimulationReportSelect(coordinator, entry), ControlModeSelect(coordinator, entry)])

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
            "safety_note": "v0.6.0-alpha-sprint6 never writes to Zendure",
        }
