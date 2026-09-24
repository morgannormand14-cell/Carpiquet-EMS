from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EMSNumber(coordinator, entry, CONF_GRID_TARGET, "Grid Target", -5000, 5000, 1),
        EMSNumber(coordinator, entry, CONF_GRID_DEADBAND, "Grid Deadband", 0, 1000, 1),
        EMSNumber(coordinator, entry, CONF_RAMP_LIMIT_W, "Ramp Limit", 0, 5000, 10),
        EMSNumber(coordinator, entry, CONF_AUTOMATION_MIN_HOLD_SECONDS, "Automation Minimum Hold", 0, 300, 1),\n        ControlledTestNumber(coordinator, entry, "power", "Controlled Test Power", 1, 100, 1, "W"),\n        ControlledTestNumber(coordinator, entry, "duration", "Controlled Test Duration", 1, 10, 1, "s"),
    ])

class EMSNumber(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry, key, name, minimum, maximum, step):
        super().__init__(coordinator)
        self._key = key
        self._entry = entry
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step

    @property
    def native_value(self):
        return float(self._entry.options.get(self._key, self.coordinator.config.get(self._key, 0)))

    async def async_set_native_value(self, value):
        options = dict(self._entry.options)
        options[self._key] = value
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        self.coordinator.config[self._key] = value
        await self.coordinator.async_request_refresh()


class ControlledTestNumber(CoordinatorEntity, NumberEntity):
    """Volatile bounded test parameter. Any change disarms the gate."""

    def __init__(self, coordinator, entry, key, name, minimum, maximum, step, unit):
        super().__init__(coordinator)
        self._test_key = key
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_controlled_test_{key}"
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        if self._test_key == "power":
            return self.coordinator.test_gate_power_w or 1.0
        return self.coordinator.test_gate_duration_seconds or 1.0

    async def async_set_native_value(self, value):
        if self._test_key == "power":
            await self.coordinator.async_set_test_gate_power(value)
        else:
            await self.coordinator.async_set_test_gate_duration(value)
