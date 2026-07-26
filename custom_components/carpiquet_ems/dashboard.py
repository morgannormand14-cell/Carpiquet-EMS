from __future__ import annotations

from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import (
    CONF_BATTERIES,
    CONF_BATTERY_ENTITIES,
    CONF_BATTERY_SERIAL,
    CONF_BATTERY_SYSTEM,
    CONF_BATTERY_TYPE,
    DASHBOARD_FILENAME,
    DASHBOARD_RELATIVE_PATH,
)

MARKER = "      # __CARPIQUET_BATTERY_CARDS__"

def _battery_cards(entry) -> str:
    blocks = []
    for battery in entry.data.get(CONF_BATTERIES, []):
        entities = battery.get(CONF_BATTERY_ENTITIES, {})
        title = f"{battery.get(CONF_BATTERY_TYPE)} {battery.get(CONF_BATTERY_SERIAL)}"
        system = "Hyper 2000" if battery.get(CONF_BATTERY_SYSTEM) == "hyper" else "SolarFlow 2400 Pro"
        rows = [
            ("soc_level", "SOC"),
            ("power", "Puissance"),
            ("batcur", "Courant"),
            ("total_vol", "Tension totale"),
            ("min_vol", "Tension cellule min"),
            ("max_vol", "Tension cellule max"),
            ("delta_voltage", "Delta cellules"),
            ("max_temp", "Température max"),
            ("state", "État BMS"),
            ("soft_version", "Firmware BMS"),
        ]
        block = [
            "      - type: grid",
            f"        title: {system} — {title}",
            "        cards:",
            "          - type: entities",
            f"            title: Batterie {title}",
            "            show_header_toggle: false",
            "            entities:",
        ]
        for key, name in rows:
            entity_id = entities.get(key)
            if entity_id:
                block.extend([
                    f"              - entity: {entity_id}",
                    f"                name: {name}",
                ])
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)

def render_dashboard(entry, template: str) -> str:
    return template.replace(MARKER, _battery_cards(entry) or "      # Aucune batterie configurée")

def install_dashboard_file(hass: HomeAssistant, entry, overwrite: bool = False) -> Path:
    source = Path(__file__).parent / "dashboard" / DASHBOARD_FILENAME
    target = Path(hass.config.path(DASHBOARD_RELATIVE_PATH))
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not overwrite:
        raise FileExistsError(str(target))

    template = source.read_text(encoding="utf-8")
    target.write_text(render_dashboard(entry, template), encoding="utf-8")
    return target
