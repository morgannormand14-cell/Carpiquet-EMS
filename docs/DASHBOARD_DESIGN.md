# Premium Dashboard Design

## User Question Model

The dashboard must answer:

1. Is the system healthy?
2. Am I importing or exporting?
3. Which battery can discharge?
4. What would the EMS request in simulation?
5. Are both batteries balanced?

## Cockpit

The Cockpit is the default operational view.

It contains:

- official identity;
- current mode;
- health score;
- grid state;
- Hyper status;
- SolarFlow status;
- balancing and user settings.

## Health Center

The Health Center exposes source availability independently of optimisation.

A source is healthy only when all required entities for that source are available.

## History

History relies on Home Assistant recorder data and uses native history cards.

## Entity Registry Note

Home Assistant preserves existing entity IDs. The dashboard assumes a clean installation with generated IDs prefixed by `carpiquet_ems`.

Existing users may need to rename entities manually or recreate the integration entry after recording configuration values.
