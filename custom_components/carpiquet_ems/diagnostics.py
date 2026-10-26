"""Privacy-preserving diagnostics for Carpiquet EMS.

Export a deliberately small set of scalar status fields. Never export raw
configuration, options, transport envelopes, MQTT payloads, or coordinator data.
"""
from .const import DOMAIN, VERSION

_SCALAR = (str, int, float, bool, type(None))
_STATUS_FIELDS = (
    "r25_cycle_mode",
    "r25_cycle_ready",
    "r25_pack_transition_execution",
    "r25_watchdog_state",
    "r25_http_result",
    "r25_dynamic_gate_state",
    "r25_dynamic_gate_target_w",
    "r25_dynamic_gate_write_allowed",
    "r25_dynamic_gate_stop_required",
)
_HTTP_FIELDS = (
    "state", "requested_w", "observed_w", "verified", "zero_verified",
    "pack_transition_confirmed",
)
_TRANSITION_FIELDS = ("state", "confirmed")
_TELEMETRY_FIELDS = (
    "entity_available", "dispatch_registered", "confirmation_state",
)
_SYSTEMS = ("hyper_2000", "solarflow_2400_pro")


def _safe_fields(value, allowed):
    """Allow only explicitly named scalar fields; drop nested/unexpected data."""
    if not isinstance(value, dict):
        return {}
    return {
        key: value[key]
        for key in allowed
        if key in value and type(value[key]) in _SCALAR
    }


def _safe_systems(data, key, allowed):
    raw = data.get(key)
    if not isinstance(raw, dict):
        return {}
    return {
        system: _safe_fields(raw[system], allowed)
        for system in _SYSTEMS
        if system in raw
    }


async def async_get_config_entry_diagnostics(hass, entry):
    """Return only whitelisted R25 state, never configuration values."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data if isinstance(coordinator.data, dict) else {}
    return {
        "version": VERSION,
        "diagnostics_schema": "r25_safe_v1",
        "state": {
            **_safe_fields(data, _STATUS_FIELDS),
            "r25_http_setpoint_feedback": _safe_fields(
                data.get("r25_http_setpoint_feedback"), _HTTP_FIELDS
            ),
            "r25_pack_transition_feedback": _safe_systems(
                data, "r25_pack_transition_feedback", _TRANSITION_FIELDS
            ),
            "r25_transition_telemetry": _safe_systems(
                data, "r25_transition_telemetry", _TELEMETRY_FIELDS
            ),
        },
    }
