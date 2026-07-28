from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SimulationSwitch(coordinator, entry), AutomationEngineSwitch(coordinator, entry)])

class SimulationSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Simulation Mode"
        self._attr_unique_id = f"{entry.entry_id}_simulation_mode"
        self._attr_icon = "mdi:test-tube"
    @property
    def is_on(self): return True
    async def async_turn_on(self, **kwargs): self.async_write_ha_state()
    async def async_turn_off(self, **kwargs): self.async_write_ha_state()

class AutomationEngineSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Automation Engine"
        self._attr_unique_id = f"{entry.entry_id}_automation_engine"
        self._attr_icon = "mdi:robot-industrial"
    @property
    def is_on(self):
        return self.coordinator.automation_enabled
    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_automation_enabled(True)
    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_automation_enabled(False)
