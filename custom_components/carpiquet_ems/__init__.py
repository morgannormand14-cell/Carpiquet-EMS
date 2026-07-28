from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import CONF_OVERWRITE, DOMAIN, SERVICE_INSTALL_DASHBOARD
from .coordinator import CarpiquetEMSCoordinator
from .dashboard import install_dashboard_file

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "switch", "select", "button"]

INSTALL_DASHBOARD_SCHEMA = vol.Schema(
    {vol.Optional(CONF_OVERWRITE, default=False): cv.boolean}
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = CarpiquetEMSCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    _register_services(hass)
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_INSTALL_DASHBOARD):
        return

    async def _install_dashboard(call: ServiceCall) -> None:
        overwrite = bool(call.data.get(CONF_OVERWRITE, False))
        try:
            target = await hass.async_add_executor_job(
                install_dashboard_file, hass, entry, overwrite
            )
        except FileExistsError as err:
            raise HomeAssistantError(
                "Le dashboard existe déjà. Activez l'option overwrite "
                "pour le remplacer."
            ) from err

        hass.components.persistent_notification.async_create(
            (
                "Le fichier Premium Dashboard a été installé dans "
                f"`{target}`. Consultez docs/DASHBOARD_INSTALLATION.md "
                "pour l'ajouter à la barre latérale."
            ),
            title="Carpiquet EMS — Dashboard prêt",
            notification_id="carpiquet_ems_dashboard_installed",
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_INSTALL_DASHBOARD,
        _install_dashboard,
        schema=INSTALL_DASHBOARD_SCHEMA,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None:
        await coordinator.async_shutdown()
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    if ok and not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_INSTALL_DASHBOARD)

    return ok
