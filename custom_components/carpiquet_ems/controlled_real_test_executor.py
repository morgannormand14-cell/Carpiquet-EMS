from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


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
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


async def _get_output(session, target: str) -> tuple[int, float | None]:
    async with session.get(target, timeout=5) as response:
        status = int(response.status)
        payload = await response.json(content_type=None) if status == 200 else {}
        return status, _output(payload)


async def _post(session, target: str, body: dict) -> int:
    async with session.post(target, json=body, timeout=5) as response:
        # Consume the response so the connection is cleanly reusable.
        await response.read()
        return int(response.status)


async def execute_single_solarflow_test(
    hass, *, test_target: str, report_target: str, test_body: dict,
    zero_body: dict, power_w: float, duration_seconds: float,
) -> RealTestResult:
    """Execute exactly one bounded SolarFlow Local HTTP test.

    Caller must enforce the 3B-21 authorization boundary. Once the test POST
    succeeds, a zero POST is attempted in finally on every path.
    """
    if not test_target.endswith("/properties/write") or not report_target.endswith("/properties/report"):
        raise ValueError("Invalid SolarFlow Local HTTP targets")
    if not (1.0 <= float(power_w) <= 100.0 and 1.0 <= float(duration_seconds) <= 10.0):
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
    test_sent = False
    try:
        test_status = await _post(session, test_target, test_body)
        test_sent = 200 <= test_status < 300
        if not test_sent:
            raise RuntimeError(f"TEST_POST_HTTP_{test_status}")
        get_status, observed = await _get_output(session, report_target)
        test_verified = bool(get_status == 200 and observed is not None and abs(observed - float(power_w)) <= 1.0)
        if not test_verified:
            raise RuntimeError("TEST_READBACK_NOT_CONFIRMED")
        await asyncio.sleep(float(duration_seconds))
    except Exception as err:
        error = f"{type(err).__name__}: {err}"
    finally:
        if test_sent:
            try:
                zero_status = await _post(session, test_target, zero_body)
                if 200 <= zero_status < 300:
                    get_status, observed = await _get_output(session, report_target)
                    zero_verified = bool(get_status == 200 and observed is not None and abs(observed) <= 1.0)
            except Exception as err:
                if not error:
                    error = f"ZERO_{type(err).__name__}: {err}"

    state = "REAL_TEST_COMPLETE_RELOCKED" if test_verified and zero_verified else "REAL_TEST_FAILED_RELOCKED"
    return RealTestResult(
        state=state, test_post_status=test_status, test_verified=test_verified,
        zero_post_status=zero_status, zero_verified=zero_verified, relocked=True,
        error=error, completed_at=datetime.now(timezone.utc).isoformat(),
    )
