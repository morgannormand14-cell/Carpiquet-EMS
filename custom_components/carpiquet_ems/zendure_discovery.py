from __future__ import annotations

"""Manual, read-only Zendure hardware discovery for Sprint 7 Step 2B.

Discovery is intentionally event driven. Nothing in this module schedules polling:
it is called only by an explicit Carpiquet synchronization action (and later by the
initial config flow). It reads Home Assistant registries; it never calls Zendure,
never writes an entity, and never changes EMS authority.
"""

from dataclasses import asdict, dataclass
from typing import Any

from homeassistant.helpers import device_registry as dr, entity_registry as er

ZENDURE_DOMAIN = "zendure_ha"

# Hardware catalogue derived from Zendure-HA product models. Infrastructure
# devices (notably Zendure Manager) are intentionally not part of this list.
HARDWARE_MODEL_PREFIXES = (
    "ace1500", "aio2400", "solarflowaiozy", "hub1200", "solarflow2.0",
    "hub2000", "solarflowhub2000", "hyper2000", "solarflow800",
    "solarflow1600", "solarflow2400", "solarflow4000", "superbasev",
)

def _is_energy_hardware(model: str, model_id: str | None = None) -> bool:
    model_key = _norm(model)
    model_id_key = _norm(model_id)
    return any(model_key.startswith(prefix) or model_id_key.startswith(prefix)
               for prefix in HARDWARE_MODEL_PREFIXES)

SEMANTIC_KEYS = {
    "electric_level": "soc",
    "min_soc": "min_soc",
    "soc_set": "max_soc",
    "total_kwh": "capacity_kwh",
    "available_kwh": "available_kwh",
    "inverse_max_power": "max_discharge_w",
    "solar_input_power": "pv_w",
    "output_home_power": "home_output_w",
    "grid_input_power": "grid_input_w",
    "output_limit": "command_limit_w",
    "input_limit": "input_limit_w",
    "connection_status": "connection_status",
    "grid_off_power": "grid_off_power_w",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "").replace("_", "")


def _control_profile(model: str) -> tuple[str, str, bool]:
    key = _norm(model)
    if key.startswith("hyper2000"):
        return "legacy", "legacy_hyper", True
    if key in {"hub1200", "solarflow2.0", "hub2000", "solarflowhub2000"}:
        return "legacy", "legacy_hub", False
    if key in {"aio2400", "solarflowaiozy"}:
        return "legacy", "legacy_aio", False
    if key.startswith("ace1500"):
        return "legacy", "legacy_ace", False
    if key.startswith("solarflow"):
        return "zensdk", "zensdk_ac", key in {"solarflow2400pro"}
    if key.startswith("superbase"):
        return "unknown", "unsupported", False
    return "unknown", "unsupported", False


def _zendure_identifier(device) -> str | None:
    for domain, value in device.identifiers:
        if domain == ZENDURE_DOMAIN and value:
            return str(value)
    return None


def _entity_translation_key(entry) -> str | None:
    key = getattr(entry, "translation_key", None)
    return str(key) if key else None


@dataclass(frozen=True)
class ZendureBatteryProfile:
    device_id: str
    zendure_id: str | None
    serial_number: str | None
    name: str
    model: str | None
    model_id: str | None
    parent_device_id: str
    entities: dict[str, str]


@dataclass(frozen=True)
class ZendureDeviceProfile:
    system_id: str
    device_id: str
    zendure_id: str | None
    serial_number: str | None
    name: str
    model: str | None
    model_id: str | None
    product_key: str | None
    protocol_device_id: str | None
    protocol_generation: str
    control_profile: str
    control_profile_supported: bool
    entities: dict[str, str]
    batteries: tuple[ZendureBatteryProfile, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)



def enrich_validated_inventory_routing_metadata(hass, inventory: dict[str, Any]) -> dict[str, Any]:
    """Enrich saved validated systems with public HA registry routing metadata.

    This is deliberately NOT hardware discovery: it only looks up the exact
    Home Assistant device_id values already present in the validated inventory.
    It cannot add/remove systems or batteries, alter topology, or change
    authority. Missing registry devices leave the saved system unchanged.
    """
    enriched = dict(inventory)
    systems = inventory.get("systems", [])
    if not isinstance(systems, list):
        return enriched

    devices = dr.async_get(hass)
    by_id = {dev.id: dev for dev in devices.devices}
    enriched_systems = []

    for saved in systems:
        if not isinstance(saved, dict):
            enriched_systems.append(saved)
            continue

        row = dict(saved)
        device_id = str(row.get("device_id") or "")
        dev = by_id.get(device_id)
        if dev is not None:
            is_zendure = (
                str(getattr(dev, "manufacturer", "") or "").casefold() == "zendure"
                or any(domain == ZENDURE_DOMAIN for domain, _ in dev.identifiers)
            )
            if is_zendure:
                row["product_key"] = getattr(dev, "model_id", None)
                row["protocol_device_id"] = getattr(dev, "hw_version", None)

        enriched_systems.append(row)

    enriched["systems"] = enriched_systems
    enriched["routing_metadata_enriched"] = True
    return enriched


def discover_zendure_inventory(hass) -> dict[str, Any]:
    """Read HA registries once and return a normalized Zendure inventory."""
    devices = dr.async_get(hass)
    entities = er.async_get(hass)

    zendure_devices = {
        dev.id: dev
        for dev in devices.devices
        if str(getattr(dev, "manufacturer", "") or "").casefold() == "zendure"
        or any(domain == ZENDURE_DOMAIN for domain, _ in dev.identifiers)
    }

    by_device: dict[str, dict[str, str]] = {device_id: {} for device_id in zendure_devices}
    for entry in entities.entities.values():
        if entry.device_id not in by_device or entry.platform != ZENDURE_DOMAIN:
            continue
        translation_key = _entity_translation_key(entry)
        if translation_key:
            semantic = SEMANTIC_KEYS.get(translation_key)
            if semantic:
                by_device[entry.device_id][semantic] = entry.entity_id

    roots = []
    infrastructure = []
    for device_id, dev in zendure_devices.items():
        parent_id = getattr(dev, "via_device_id", None)
        if parent_id and parent_id in zendure_devices:
            continue

        # A root Zendure registry device is not necessarily energy hardware.
        # Zendure Manager is also a root device; classify by model/product model
        # rather than by display name so infrastructure never enters systems[].
        if not _is_energy_hardware(str(dev.model or ""), getattr(dev, "model_id", None)):
            infrastructure.append({
                "device_id": device_id,
                "name": dev.name_by_user or dev.name or device_id,
                "model": dev.model,
                "model_id": getattr(dev, "model_id", None),
                "classification": "infrastructure_ignored",
            })
            continue

        serial = getattr(dev, "serial_number", None)
        zendure_id = _zendure_identifier(dev)
        stable = str(serial or zendure_id or device_id)
        protocol, control_profile, supported = _control_profile(str(dev.model or ""))
        batteries = []
        for child_id, child in zendure_devices.items():
            if getattr(child, "via_device_id", None) != device_id:
                continue
            batteries.append(ZendureBatteryProfile(
                device_id=child_id,
                zendure_id=_zendure_identifier(child),
                serial_number=getattr(child, "serial_number", None),
                name=child.name or child.name_by_user or child_id,
                model=child.model,
                model_id=getattr(child, "model_id", None),
                parent_device_id=device_id,
                entities=dict(sorted(by_device.get(child_id, {}).items())),
            ))

        roots.append(ZendureDeviceProfile(
            system_id=f"zendure:{stable}",
            device_id=device_id,
            zendure_id=zendure_id,
            serial_number=serial,
            name=dev.name_by_user or dev.name or stable,
            model=dev.model,
            model_id=getattr(dev, "model_id", None),
            product_key=getattr(dev, "model_id", None),
            protocol_device_id=getattr(dev, "hw_version", None),
            protocol_generation=protocol,
            control_profile=control_profile,
            control_profile_supported=supported,
            entities=dict(sorted(by_device.get(device_id, {}).items())),
            batteries=tuple(sorted(batteries, key=lambda b: (b.serial_number or "", b.device_id))),
        ))

    systems = [profile.as_dict() for profile in sorted(roots, key=lambda p: p.system_id)]
    return {
        "mode": "manual_read_only",
        "trigger": "manual_sync",
        "periodic_discovery": False,
        "writes_enabled": False,
        "authority": False,
        "systems_count": len(systems),
        "batteries_count": sum(len(row["batteries"]) for row in systems),
        "supported_control_profiles_count": sum(bool(row["control_profile_supported"]) for row in systems),
        "infrastructure_count": len(infrastructure),
        "infrastructure": sorted(infrastructure, key=lambda row: (str(row.get("name") or ""), row["device_id"])),
        "systems": systems,
    }


def _battery_key(row: dict[str, Any]) -> str:
    return str(row.get("serial_number") or row.get("zendure_id") or row.get("device_id") or "")

def compare_zendure_inventories(saved: dict[str, Any] | None, detected: dict[str, Any]) -> dict[str, Any]:
    """Compare stable hardware identities only; availability is deliberately ignored."""
    saved = saved or {}
    old = {str(s.get("system_id")): s for s in saved.get("systems", []) if s.get("system_id")}
    new = {str(s.get("system_id")): s for s in detected.get("systems", []) if s.get("system_id")}
    added = sorted(set(new) - set(old))
    missing = sorted(set(old) - set(new))
    changed = []
    unchanged = []
    for sid in sorted(set(old) & set(new)):
        a, b = old[sid], new[sid]
        old_b = {_battery_key(x) for x in a.get("batteries", [])}
        new_b = {_battery_key(x) for x in b.get("batteries", [])}
        signature_a = (str(a.get("model") or ""), str(a.get("model_id") or ""), old_b)
        signature_b = (str(b.get("model") or ""), str(b.get("model_id") or ""), new_b)
        (changed if signature_a != signature_b else unchanged).append(sid)
    return {
        "identical": not added and not missing and not changed,
        "added_system_ids": added,
        "missing_system_ids": missing,
        "changed_system_ids": changed,
        "unchanged_system_ids": unchanged,
        "saved_systems_count": len(old),
        "detected_systems_count": len(new),
        "saved_batteries_count": int(saved.get("batteries_count", 0)),
        "detected_batteries_count": int(detected.get("batteries_count", 0)),
    }
