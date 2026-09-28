from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

STATE_LOCKED = "LOCKED"
STATE_READ_READY_LOCKED = "READ_READY_LOCKED"
STATE_READ_CONFIRMED_LOCKED = "READ_CONFIRMED_LOCKED"
STATE_READ_FAILED_LOCKED = "READ_FAILED_LOCKED"

REASON_TARGET_NOT_READY = "REPORT_TARGET_NOT_READY"
REASON_HTTP_STATUS = "REPORT_HTTP_STATUS_NOT_OK"
REASON_JSON = "REPORT_JSON_INVALID"
REASON_OUTPUT_MISSING = "REPORT_OUTPUT_LIMIT_MISSING"
REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"


@dataclass(frozen=True)
class ControlledReadback:
    """3B-10 read-only SolarFlow report observation.

    This object can only be produced by GET /properties/report.  The helper has
    no POST method, no /properties/write call and no command reinjection path.
    """

    state: str
    blockers: tuple[str, ...]
    target: str
    attempted: bool
    reachable: bool
    http_status: int | None
    report_available: bool
    observed_output_w: float | None
    read_confirmed: bool
    write_locked: bool
    reinjection_allowed: bool
    evaluated_at: str


def _extract_output_w(payload: Any) -> float | None:
    if not isinstance(payload, dict):
        return None
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        return None
    for key in ("outputLimit", "outputPower", "outPower"):
        value = properties.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


async def read_solarflow_report_locked(hass, target: str) -> ControlledReadback:
    """Perform one read-only GET against the already prepared report target."""
    blockers: list[str] = []
    target = str(target or "")
    if not target or not target.endswith("/properties/report"):
        blockers.extend((REASON_TARGET_NOT_READY, REASON_GLOBAL_LOCK))
        return ControlledReadback(
            state=STATE_LOCKED, blockers=tuple(blockers), target=target,
            attempted=False, reachable=False, http_status=None,
            report_available=False, observed_output_w=None, read_confirmed=False,
            write_locked=True, reinjection_allowed=False,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    try:
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        session = async_get_clientsession(hass)
        async with session.get(target, timeout=5) as response:
            status = int(response.status)
            if status != 200:
                blockers.extend((REASON_HTTP_STATUS, REASON_GLOBAL_LOCK))
                return ControlledReadback(
                    state=STATE_READ_FAILED_LOCKED, blockers=tuple(blockers),
                    target=target, attempted=True, reachable=True,
                    http_status=status, report_available=False,
                    observed_output_w=None, read_confirmed=False,
                    write_locked=True, reinjection_allowed=False,
                    evaluated_at=datetime.now(timezone.utc).isoformat(),
                )
            try:
                payload = await response.json(content_type=None)
            except Exception:
                blockers.extend((REASON_JSON, REASON_GLOBAL_LOCK))
                return ControlledReadback(
                    state=STATE_READ_FAILED_LOCKED, blockers=tuple(blockers),
                    target=target, attempted=True, reachable=True,
                    http_status=status, report_available=False,
                    observed_output_w=None, read_confirmed=False,
                    write_locked=True, reinjection_allowed=False,
                    evaluated_at=datetime.now(timezone.utc).isoformat(),
                )

            properties_ok = isinstance(payload, dict) and isinstance(payload.get("properties"), dict)
            observed = _extract_output_w(payload)
            if not properties_ok:
                blockers.append(REASON_JSON)
            if observed is None:
                blockers.append(REASON_OUTPUT_MISSING)
            blockers.append(REASON_GLOBAL_LOCK)
            confirmed = properties_ok and observed is not None
            return ControlledReadback(
                state=STATE_READ_CONFIRMED_LOCKED if confirmed else STATE_READ_READY_LOCKED,
                blockers=tuple(blockers), target=target, attempted=True,
                reachable=True, http_status=status, report_available=properties_ok,
                observed_output_w=observed, read_confirmed=confirmed,
                write_locked=True, reinjection_allowed=False,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            )
    except Exception:
        blockers.extend(("REPORT_GET_FAILED", REASON_GLOBAL_LOCK))
        return ControlledReadback(
            state=STATE_READ_FAILED_LOCKED, blockers=tuple(blockers), target=target,
            attempted=True, reachable=False, http_status=None,
            report_available=False, observed_output_w=None, read_confirmed=False,
            write_locked=True, reinjection_allowed=False,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )
