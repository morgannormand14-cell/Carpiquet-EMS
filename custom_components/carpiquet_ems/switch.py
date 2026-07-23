from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SimulationSwitch(coordinator, entry)])

class SimulationSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Simulation Mode"
        self._attr_unique_id = f"{entry.entry_id}_simulation_mode"
        self._attr_entity_id = "switch.carpiquet_ems_simulation_mode"
        self._is_on = True

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = True
        self.async_write_ha_state()
