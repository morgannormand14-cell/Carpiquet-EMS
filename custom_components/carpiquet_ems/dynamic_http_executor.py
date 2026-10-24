"""R25 SolarFlow dynamic Local HTTP transport.

This module is deliberately NOT wired to the coordinator.  Its explicit
lifecycle must be integrated with a watchdog and authorization gate before
any real hardware use. R24 one-shot execution is unaffected.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass
from math import isfinite
from time import monotonic
from typing import Any

from .controlled_real_test_executor import _get_output, _post, _restore_zero

SETTLE_SECONDS = 5.0
MAX_POWER_W = 2400.0


@dataclass(frozen=True)
class DynamicHttpResult:
    state: str
    requested_w: float
    observed_w: float | None
    post_status: int | None
    verified: bool
    zero_verified: bool
    error: str


class DynamicHttpExecutor:
    """Serialized commands; fail closed, requiring explicit start and stop.

    Only one command can be in flight. A failure latches FAULT and attempts
    physical zero; a new session must be explicitly started after inspection.
    No automatic retry of nonzero power is performed.
    """

    def __init__(self, hass: Any, *, write_target: str, report_target: str,
                 envelope: dict, limit_w: float):
        if not write_target.endswith("/properties/write"):
            raise ValueError("Invalid write endpoint")
        if not report_target.endswith("/properties/report"):
            raise ValueError("Invalid report endpoint")
        if not isfinite(float(limit_w)) or not 0 < float(limit_w) <= MAX_POWER_W:
            raise ValueError("Invalid power ceiling")
        if not isinstance(envelope, dict) or not envelope.get("id") or not envelope.get("sn"):
            raise ValueError("Missing device identity")
        if not isinstance(envelope.get("properties"), dict) or "outputLimit" not in envelope["properties"]:
            raise ValueError("Missing outputLimit")
        self.hass = hass
        self.write_target = write_target
        self.report_target = report_target
        self.envelope = deepcopy(envelope)
        self.limit_w = float(limit_w)
        self._lock = asyncio.Lock()
        self._active = False
        self._fault = False
        self._last_verified_w = 0.0
        self._last_verified_at: float | None = None

    @property
    def active(self) -> bool:
        return self._active

    @property
    def fault(self) -> bool:
        return self._fault

    def _body(self, watts: float) -> dict:
        body = deepcopy(self.envelope)
        body["properties"]["outputLimit"] = watts
        return body

    def start(self, *, authorized: bool) -> None:
        """Prepare a new session; caller must enforce external interlocks."""
        if not authorized or self._fault or self._active:
            raise RuntimeError("Dynamic session not admissible")
        self._active = True

    async def apply(self, watts: float, *, authorized: bool, conditions_valid: bool) -> DynamicHttpResult:
        async with self._lock:
            if not self._active or self._fault:
                raise RuntimeError("Dynamic session locked")
            if not authorized or not conditions_valid:
                return await self._stop_locked("INTERLOCK_LOST")
            if not isfinite(float(watts)) or not 0 <= float(watts) <= self.limit_w:
                return await self._stop_locked("POWER_INVALID")
            if watts == 0:
                return await self._stop_locked("ZERO_REQUESTED")
            from homeassistant.helpers.aiohttp_client import async_get_clientsession
            session = async_get_clientsession(self.hass)
            status = None
            observed = None
            try:
                status = await _post(session, self.write_target, self._body(float(watts)))
                if not 200 <= status < 300:
                    raise RuntimeError(f"POST_HTTP_{status}")
                await asyncio.sleep(SETTLE_SECONDS)
                get_status, observed = await _get_output(session, self.report_target)
                if get_status != 200 or observed is None or abs(observed - float(watts)) > 1.0:
                    raise RuntimeError("READBACK_NOT_CONFIRMED")
                self._last_verified_w = float(watts)
                self._last_verified_at = monotonic()
                return DynamicHttpResult("APPLIED_VERIFIED", float(watts), observed, status, True, False, "")
            except BaseException as exc:
                # Even a cancelled/timed-out POST might have reached hardware.
                self._fault = True
                self._active = False
                recovery = asyncio.create_task(
                    _restore_zero(session, self.write_target, self.report_target, self._body(0.0))
                )
                try:
                    zero_status, zero_ok, zero_error = await asyncio.shield(recovery)
                except asyncio.CancelledError:
                    await recovery
                    raise
                if isinstance(exc, asyncio.CancelledError):
                    raise
                return DynamicHttpResult(
                    "FAULT_ZERO_VERIFIED" if zero_ok else "FAULT_ZERO_UNCONFIRMED",
                    float(watts), observed, status, False, zero_ok,
                    f"{type(exc).__name__}: {exc}; {zero_error}".strip("; "),
                )

    async def stop(self, *, reason: str = "MANUAL_STOP") -> DynamicHttpResult:
        async with self._lock:
            return await self._stop_locked(reason)

    async def _stop_locked(self, reason: str) -> DynamicHttpResult:
        self._active = False
        from homeassistant.helpers.aiohttp_client import async_get_clientsession
        session = async_get_clientsession(self.hass)
        recovery = asyncio.create_task(
            _restore_zero(session, self.write_target, self.report_target, self._body(0.0))
        )
        try:
            status, verified, error = await asyncio.shield(recovery)
        except asyncio.CancelledError:
            await recovery
            raise
        if not verified:
            self._fault = True
        else:
            self._last_verified_w = 0.0
            self._last_verified_at = monotonic()
        return DynamicHttpResult(
            "STOP_ZERO_VERIFIED" if verified else "STOP_ZERO_UNCONFIRMED",
            0.0, 0.0 if verified else None, status, False, verified,
            f"{reason}: {error}" if error else reason,
        )
