from __future__ import annotations

import re

COMMON_SUFFIXES = (
    "batcur",
    "delta_voltage",
    "max_temp",
    "max_vol",
    "min_vol",
    "power",
    "soc_level",
    "soft_version",
    "state",
    "total_vol",
)

def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")

def battery_prefix(battery_type: str, serial: str) -> str:
    return f"{normalize_token(battery_type)}_{normalize_token(serial)}"

def build_battery_entities(battery_type: str, serial: str) -> dict[str, str]:
    prefix = battery_prefix(battery_type, serial)
    entities = {suffix: f"sensor.{prefix}_{suffix}" for suffix in COMMON_SUFFIXES}
    # SolarFlow I2400 / AB3000L expose pack_type. Harmless to validate/use when present.
    entities["pack_type"] = f"sensor.{prefix}_pack_type"
    return entities

def valid_numeric(value, minimum=None, maximum=None) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    if number != number:  # NaN
        return False
    if minimum is not None and number < minimum:
        return False
    if maximum is not None and number > maximum:
        return False
    return True
