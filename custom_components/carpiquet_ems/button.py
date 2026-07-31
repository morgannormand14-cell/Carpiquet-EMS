from homeassistant.components.button import ButtonEntity
from homeassistant.components import persistent_notification
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PrepareReportButton(coordinator, entry)])

class PrepareReportButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Prepare Simulation Report"
        self._attr_unique_id = f"{entry.entry_id}_prepare_simulation_report"
        self._attr_icon = "mdi:download"

    async def async_press(self):
        url = await self.coordinator.async_prepare_selected_report()
        # The report preparation must never depend on notifications.
        try:
            if url:
                persistent_notification.async_create(
                    self.hass,
                    f"Rapport prêt : `{url}`\n\nOuvrez cette adresse depuis Home Assistant pour télécharger le JSON.",
                    title="Carpiquet EMS — Rapport prêt",
                    notification_id="carpiquet_ems_report_ready",
                )
            else:
                persistent_notification.async_create(
                    self.hass,
                    "Aucun rapport de simulation n'est disponible.",
                    title="Carpiquet EMS — Aucun rapport",
                    notification_id="carpiquet_ems_report_ready",
                )
        except Exception:
            pass
        await self.coordinator.async_request_refresh()
