from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SimulationSwitch(coordinator, entry), AutomationEngineSwitch(coordinator, entry), ControlledTestArmSwitch(coordinator, entry), ControlledTestAuthorizationSimulationSwitch(coordinator, entry), ControlledRealTestAuthorizationSwitch(coordinator, entry), R25RealCycleSwitch(coordinator, entry)])

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


class ControlledTestArmSwitch(CoordinatorEntity, SwitchEntity):
    """Arm the test configuration only. This switch never grants execution."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Controlled Test Arm"
        self._attr_unique_id = f"{entry.entry_id}_controlled_test_arm"
        self._attr_icon = "mdi:shield-lock"

    @property
    def is_on(self):
        return self.coordinator.test_gate_armed

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_test_gate_armed(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_test_gate_armed(False)

    @property
    def extra_state_attributes(self):
        return {
            "execution_enabled": False,
            "global_write_lock": True,
            "note": "ARMED_LOCKED configuration only; no hardware I/O path",
        }


class ControlledTestAuthorizationSimulationSwitch(CoordinatorEntity, SwitchEntity):
    """Simulate explicit Phase 3B authorization without enabling hardware writes."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Controlled Test Authorization Simulation"
        self._attr_unique_id = f"{entry.entry_id}_controlled_test_authorization_simulation"
        self._attr_icon = "mdi:shield-check-outline"

    @property
    def is_on(self):
        return self.coordinator.test_sequence_authorized

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_test_sequence_authorized(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_test_sequence_authorized(False)

    @property
    def extra_state_attributes(self):
        return {
            "simulation_only": True,
            "execution_enabled": False,
            "global_write_lock": True,
            "note": "Phase 3B Step 4 authorization simulation only; no hardware I/O path",
        }

class ControlledRealTestAuthorizationSwitch(CoordinatorEntity, SwitchEntity):
    """Volatile second key for the one-shot 3B-21 real SolarFlow test."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Real Test Authorization"
        self._attr_unique_id = f"{entry.entry_id}_controlled_real_test_authorization"
        self._attr_icon = "mdi:shield-key"

    @property
    def is_on(self):
        return self.coordinator.real_test_authorized

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_real_test_authorized(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_real_test_authorized(False)

    @property
    def extra_state_attributes(self):
        return {"volatile": True, "one_shot": True, "scope": "SolarFlow frozen EMS setpoint within operator ceiling"}


class R25RealCycleSwitch(CoordinatorEntity, SwitchEntity):
    """Operator-facing mode switch; real output stays locked until commissioning."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS R25 Cycle Reel"
        self._attr_unique_id = f"{entry.entry_id}_r25_real_cycle"
        self._attr_icon = "mdi:shield-lock-outline"

    @property
    def is_on(self):
        return self.coordinator.r25_cycle_mode == "Cycle réel"

    async def async_turn_on(self, **kwargs):
        from homeassistant.exceptions import HomeAssistantError
        try:
            await self.coordinator.async_set_r25_cycle_mode(True)
        except RuntimeError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_r25_cycle_mode(False)

    @property
    def extra_state_attributes(self):
        return {
            "mode_off": "Simulation",
            "mode_on": "Cycle réel",
            "real_cycle_available": bool(self.coordinator.data and self.coordinator.data.get("r25_cycle_ready")),
            "cycle_mode": self.coordinator.r25_cycle_mode,
            "reason": "Requires fresh EMS inputs, qualified SolarFlow local HTTP and verified SOC",
            "hardware_writes_enabled": self.is_on,
        }
