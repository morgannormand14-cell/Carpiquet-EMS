from homeassistant.components.button import ButtonEntity
from homeassistant.components import persistent_notification
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .dashboard import install_dashboard_file


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PrepareReportButton(coordinator, entry),
            SynchronizeCarpiquetButton(coordinator, entry),
        ]
    )


class PrepareReportButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_name = "Carpiquet EMS Prepare Simulation Report"
        self._attr_unique_id = f"{entry.entry_id}_prepare_simulation_report"
        self._attr_icon = "mdi:download"

    async def async_press(self):
        url = await self.coordinator.async_prepare_selected_report()
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


class SynchronizeCarpiquetButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Carpiquet EMS Synchroniser Carpiquet EMS"
        # Keep the old unique_id so existing HA entity customizations survive.
        self._attr_unique_id = f"{entry.entry_id}_regenerate_dashboard"
        self._attr_icon = "mdi:sync"

    async def async_press(self):
        try:
            result = await self.coordinator.async_sync_zendure_inventory()
            discovery = result["snapshot"]
            comparison = result["comparison"]
            target = None
            if comparison.get("identical"):
                target = await self.hass.async_add_executor_job(
                    install_dashboard_file, self.hass, self._entry, True
                )
        except Exception as err:
            persistent_notification.async_create(
                self.hass,
                f"Échec de la synchronisation Carpiquet EMS : `{err}`",
                title="Carpiquet EMS — Erreur synchronisation",
                notification_id="carpiquet_ems_synchronization",
            )
            raise HomeAssistantError(
                f"Impossible de synchroniser Carpiquet EMS : {err}"
            ) from err

        systems = discovery.get("systems_count", 0)
        batteries = discovery.get("batteries_count", 0)
        if comparison.get("identical"):
            message = (
                f"Inventaire Zendure identique : **{systems} système(s)** et "
                f"**{batteries} batterie(s)**. Aucune modification matérielle.\n\n"
                f"Dashboard régénéré dans `{target}`."
            )
        else:
            message = (
                f"Modification matérielle détectée : **{systems} système(s)** et "
                f"**{batteries} batterie(s)** actuellement détectés.\n\n"
                "L'inventaire Carpiquet validé reste inchangé. Ouvrez "
                "**Paramètres → Appareils et services → Carpiquet EMS → Configurer** "
                "pour examiner puis **Valider** ou **Refuser** les changements.\n\n"
                "Le Dashboard n'a pas été modifié."
            )
        persistent_notification.async_create(
            self.hass, message,
            title="Carpiquet EMS — Synchronisation terminée",
            notification_id="carpiquet_ems_synchronization",
        )
