# Installation

## HACS

1. Add `morgannormand14-cell/Carpiquet-EMS` as a custom integration repository.
2. Download the Sprint 3 pre-release.
3. Restart Home Assistant.
4. Add **Carpiquet EMS** from **Settings → Devices & services**.
5. Select the Shelly and Zendure entities using the entity pickers.
6. Keep simulation mode enabled.
7. Install the Premium Dashboard using `carpiquet_ems.install_dashboard`.
8. Follow `docs/DASHBOARD_INSTALLATION.md`.

## Updating the configuration

Open:

**Settings → Devices & services → Carpiquet EMS → Configure**

The Options Flow allows the source entities and EMS parameters to be changed
without removing the integration.

## Upgrade notes

Home Assistant preserves entity IDs in its entity registry. Existing entity IDs
are not renamed automatically during an update.
