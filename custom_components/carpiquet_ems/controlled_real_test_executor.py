from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

ZERO_ATTEMPTS = 3
SETTLING_SECONDS = 5.0


@dataclass(frozen=True)
class RealTestResult:
    state: str
    test_post_status: int | None
    test_verified: bool
    zero_post_status: int | None
    zero_verified: bool
    relocked: bool
    error: str
    completed_at: str


def _output(payload: Any) -> float | None:
    if not isinstance(payload, dict) or not isinstance(payload.get("properties"), dict):
        return None
    for key in ("outputLimit", "outputPower", "outPower"):
        value = payload["properties"].get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            return float(value)
    return None


async def _get_output(session, target: str) -> tuple[int, float | None]:
    async with session.get(target, timeout=5) as response:
        status = int(response.status)
        payload = await response.json(content_type=None) if status == 200 else {}
        return status, _output(payload)


async def _post(session, target: str, body: dict) -> int:
    async with session.post(target, json=body, timeout=5) as response:
        await response.read()
        return int(response.status)


async def _restore_zero(session, test_target: str, report_target: str, zero_body: dict):
    """Bounded zero recovery; verify readback even if POST response is lost."""
    last_status = None
    errors = []
    for attempt in range(1, ZERO_ATTEMPTS + 1):
        try:
            last_status = await _post(session, test_target, zero_body)
            if not 200 <= last_status < 300:
                errors.append(f"ZERO_POST_HTTP_{last_status}_ATTEMPT_{attempt}")
        except Exception as err:
            errors.append(f"ZERO_POST_{type(err).__name__}_ATTEMPT_{attempt}: {err}")
        # A timed-out POST can still have been applied: always attempt readback.
        await asyncio.sleep(SETTLING_SECONDS)
        try:
            status, observed = await _get_output(session, report_target)
            if status == 200 and observed is not None and abs(observed) <= 1.0:
                return last_status, True, ""
            errors.append(f"ZERO_READBACK_UNCONFIRMED_ATTEMPT_{attempt}")
        except Exception as err:
            errors.append(f"ZERO_GET_{type(err).__name__}_ATTEMPT_{attempt}: {err}")
    return last_status, False, "; ".join(errors)


async def execute_single_solarflow_test(
    hass, *, test_target: str, report_target: str, test_body: dict,
    zero_body: dict, power_w: float, duration_seconds: float,
) -> RealTestResult:
    """One authorized SolarFlow test; always attempt zero after initiating POST.

    Software authorization is revoked by the coordinator independently of
    physical zero confirmation. Unconfirmed zero must remain visible as failure.
    """
    if not test_target.endswith("/properties/write") or not report_target.endswith("/properties/report"):
        raise ValueError("Invalid SolarFlow Local HTTP targets")
    if not (
        math.isfinite(float(power_w)) and 0.0 < float(power_w) <= 2400.0
        and math.isfinite(float(duration_seconds)) and 0.0 <= float(duration_seconds) <= 600.0
    ):
        raise ValueError("Controlled test outside safety bounds")
    if float(test_body.get("properties", {}).get("outputLimit", -1)) != float(power_w):
        raise ValueError("Prepared test body does not match requested power")
    if float(zero_body.get("properties", {}).get("outputLimit", -1)) != 0.0:
        raise ValueError("Mandatory zero body is invalid")

    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    session = async_get_clientsession(hass)
    test_status = None
    zero_status = None
    test_verified = False
    zero_verified = False
    error = ""
    post_attempted = False
    try:
        # Mark before I/O: a timeout or cancellation does not prove no write occurred.
        post_attempted = True
        test_status = await _post(session, test_target, test_body)
        if not 200 <= test_status < 300:
            raise RuntimeError(f"TEST_POST_HTTP_{test_status}")
        await asyncio.sleep(SETTLING_SECONDS)
        get_status, observed = await _get_output(session, report_target)
        test_verified = bool(
            get_status == 200 and observed is not None
            and abs(observed - float(power_w)) <= 1.0
        )
        if not test_verified:
            raise RuntimeError("TEST_READBACK_NOT_CONFIRMED")
        await asyncio.sleep(float(duration_seconds))
    except Exception as err:
        error = f"{type(err).__name__}: {err}"
    finally:
        if post_attempted:
            # Shield cleanup from caller cancellation, and wait for it to finish
            # before returning/re-raising; never abandon the zero operation.
            recovery = asyncio.create_task(
                _restore_zero(session, test_target, report_target, zero_body)
            )
            try:
                zero_status, zero_verified, zero_error = await asyncio.shield(recovery)
            except asyncio.CancelledError:
                # Python task cancellation must not orphan the physical stop.
                zero_status, zero_verified, zero_error = await recovery
                raise
            if zero_error:
                error = f"{error}; {zero_error}".strip("; ")

    if zero_verified:
        state = "REAL_TEST_COMPLETE_RELOCKED" if test_verified else "REAL_TEST_FAILED_RELOCKED"
    else:
        state = "ZERO_UNCONFIRMED_RELOCKED"
    return RealTestResult(
        state=state, test_post_status=test_status, test_verified=test_verified,
        zero_post_status=zero_status, zero_verified=zero_verified, relocked=True,
        error=error, completed_at=datetime.now(timezone.utc).isoformat(),
    )
