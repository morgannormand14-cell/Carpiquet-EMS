from __future__ import annotations
from pathlib import Path
from typing import Any
from homeassistant.core import HomeAssistant
from .const import CONF_BATTERIES, CONF_BATTERY_ENTITIES, CONF_BATTERY_SERIAL, CONF_BATTERY_SYSTEM, CONF_BATTERY_TYPE, DASHBOARD_FILENAME, DASHBOARD_RELATIVE_PATH
from .entity_mapper import build_shadow_systems

BATTERY_MARKER="      # __CARPIQUET_BATTERY_CARDS__"
COCKPIT_MARKER="      # __CARPIQUET_DYNAMIC_SYSTEM_CARDS__"
ZENDURE_MARKER="      # __CARPIQUET_DYNAMIC_ZENDURE_CARDS__"
HEALTH_MARKER="              # __CARPIQUET_DYNAMIC_HEALTH_ROWS__"
HISTORY_MARKER="      # __CARPIQUET_DYNAMIC_HISTORY_CARDS__"

def _safe_systems(systems):
    items=list(systems or [])
    if not 1 <= len(items) <= 5:
        raise ValueError(f"Dynamic Dashboard supports 1..5 systems, got {len(items)}")
    return items

def _rows(entities,specs,indent):
    out=[]
    for key,label in specs:
        entity_id=entities.get(key)
        if entity_id:
            out.extend((f"{indent}- entity: {entity_id}",f"{indent}  name: {label}"))
    return out

def _system_cards(systems):
    specs=(("pv_w","Puissance PV"),("home_output_w","Puissance vers maison"),("grid_input_w","Entrée réseau"),
           ("capacity_kwh","Capacité totale"),("max_power_w","Puissance maximale"),("min_soc","SOC minimum"),("max_soc","SOC maximum"))
    blocks=[]
    for s in systems:
        e=s.get("entities",{}); name=s.get("name") or s.get("system_id") or "Système Zendure"
        b=["      - type: grid",f"        title: {name}","        cards:"]
        if e.get("soc"):
            b.extend(("          - type: gauge",f"            entity: {e['soc']}",f"            name: SOC {name}","            min: 0","            max: 100"))
        b.extend(("          - type: entities","            show_header_toggle: false","            entities:"))
        b.extend(_rows(e,specs,"              ")); blocks.append("\n".join(b))
    return "\n\n".join(blocks)

def _zendure_cards(systems):
    specs=(("soc","SOC Zendure natif"),("capacity_kwh","Capacité totale"),("max_power_w","Puissance maximale"),
           ("min_soc","SOC minimum"),("max_soc","SOC maximum"),("pv_w","Puissance PV"),("home_output_w","Puissance vers maison"),
           ("grid_input_w","Entrée réseau"),("command_limit_w","Limite / commande native"))
    blocks=[]
    for s in systems:
        e=s.get("entities",{}); name=s.get("name") or s.get("system_id") or "Système Zendure"
        b=["      - type: grid",f"        title: {name} — Zendure","        cards:","          - type: entities",
           "            show_header_toggle: false","            entities:"]
        b.extend(_rows(e,specs,"              ")); blocks.append("\n".join(b))
    return "\n\n".join(blocks)

def _health_rows(systems):
    out=[]
    for s in systems:
        eid=s.get("entities",{}).get("soc")
        if eid:
            name=s.get("name") or s.get("system_id") or "Système Zendure"
            out.extend((f"              - entity: {eid}",f"                name: {name} — télémétrie SOC"))
    return "\n".join(out) or "              # Aucun système disponible"

def _history_cards(systems):
    soc=[s.get("entities",{}).get("soc") for s in systems if s.get("entities",{}).get("soc")]
    pv=[s.get("entities",{}).get("pv_w") for s in systems if s.get("entities",{}).get("pv_w")]
    out=[]
    if soc:
        out.extend(("      - type: history-graph","        title: SOC systèmes — 24 h","        hours_to_show: 24","        entities:"))
        out.extend(f"          - {x}" for x in soc)
    if pv:
        if out: out.append("")
        out.extend(("      - type: history-graph","        title: Production PV systèmes — 24 h","        hours_to_show: 24","        entities:"))
        out.extend(f"          - {x}" for x in pv)
    return "\n".join(out) or "      # Aucun historique système disponible"

def _battery_cards(entry):
    blocks=[]
    specs=(("soc_level","SOC"),("power","Puissance"),("batcur","Courant"),("total_vol","Tension totale"),
           ("min_vol","Tension cellule min"),("max_vol","Tension cellule max"),("delta_voltage","Delta cellules"),
           ("max_temp","Température max"),("state","État BMS"),("soft_version","Firmware BMS"))
    for battery in entry.data.get(CONF_BATTERIES,[]):
        e=battery.get(CONF_BATTERY_ENTITIES,{})
        title=f"{battery.get(CONF_BATTERY_TYPE)} {battery.get(CONF_BATTERY_SERIAL)}"
        system=str(battery.get(CONF_BATTERY_SYSTEM) or "Système").replace("_"," ").title()
        b=["      - type: grid",f"        title: {system} — {title}","        cards:","          - type: entities",
           f"            title: Batterie {title}","            show_header_toggle: false","            entities:"]
        b.extend(_rows(e,specs,"              ")); blocks.append("\n".join(b))
    return "\n\n".join(blocks)

def render_dashboard(entry,template,systems=None):
    rendered=template.replace(BATTERY_MARKER,_battery_cards(entry) or "      # Aucune batterie configurée")
    if systems is not None:
        systems=_safe_systems(systems)
        rendered=rendered.replace(COCKPIT_MARKER,_system_cards(systems))
        rendered=rendered.replace(ZENDURE_MARKER,_zendure_cards(systems))
        rendered=rendered.replace(HEALTH_MARKER,_health_rows(systems))
        rendered=rendered.replace(HISTORY_MARKER,_history_cards(systems))
    return rendered

def install_dashboard_file(hass: HomeAssistant,entry,overwrite=False):
    source=Path(__file__).parent/"dashboard"/DASHBOARD_FILENAME
    target=Path(hass.config.path(DASHBOARD_RELATIVE_PATH)); target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and not overwrite: raise FileExistsError(str(target))
    systems=build_shadow_systems(hass,entry.data|entry.options)
    target.write_text(render_dashboard(entry,source.read_text(encoding="utf-8"),systems),encoding="utf-8")
    return target
