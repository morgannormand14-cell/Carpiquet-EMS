# Installation

## HACS

1. Add `morgannormand14-cell/Carpiquet-EMS` as a custom integration repository.
2. Download the latest release.
3. Restart Home Assistant.
4. Add **Carpiquet EMS** from **Settings → Devices & services**.
5. Configure the Shelly and Zendure entity IDs.
6. Keep simulation mode enabled.

## Upgrade Notes

Home Assistant preserves entity IDs in its entity registry. Renaming entity display names in code does not automatically rename existing entity IDs.

For a clean alpha migration, remove and recreate the integration entry only after recording the configuration values.
