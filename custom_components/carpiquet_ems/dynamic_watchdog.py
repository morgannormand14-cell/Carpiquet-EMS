"""R25 monotonic-clock watchdog for an explicitly authorized dynamic session.

This watchdog is NOT started by Home Assistant yet. The future session owner
must start it, feed fresh EMS decisions, and stop it on unload. Its stop
callback must perform a verified physical zero (DynamicHttpExecutor.stop).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Awaitable, Callable

DEFAULT_DECISION_TIMEOUT = 30.0
DEFAULT_CONFIRMATION_TIMEOUT = 30.0
DEFAULT_POLL_INTERVAL = 1.0


@dataclass(frozen=True)
class WatchdogStatus:
    state: str
    reason: str
    last_decision_age_s: float | None
    last_confirmation_age_s: float | None
    stop_confirmed: bool | None


class DynamicWatchdog:
    def __init__(
        self,
        *,
        stop_callback: Callable[[str], Awaitable[object]],
        decision_timeout_s: float = DEFAULT_DECISION_TIMEOUT,
        confirmation_timeout_s: float = DEFAULT_CONFIRMATION_TIMEOUT,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL,
        clock: Callable[[], float] = monotonic,
    ):
        if min(decision_timeout_s, confirmation_timeout_s, poll_interval_s) <= 0:
            raise ValueError("Watchdog intervals must be positive")
        self._stop_callback = stop_callback
        self._decision_timeout = float(decision_timeout_s)
        self._confirmation_timeout = float(confirmation_timeout_s)
        self._poll_interval = float(poll_interval_s)
        self._clock = clock
        self._last_decision: float | None = None
        self._last_confirmation: float | None = None
        self._task: asyncio.Task | None = None
        self._state = "LOCKED"
        self._reason = ""
        self._stop_confirmed: bool | None = None
        self._trip_lock = asyncio.Lock()

    @property
    def status(self) -> WatchdogStatus:
        now = self._clock()
        return WatchdogStatus(
            self._state, self._reason,
            None if self._last_decision is None else max(0.0, now - self._last_decision),
            None if self._last_confirmation is None else max(0.0, now - self._last_confirmation),
            self._stop_confirmed,
        )

    def start(self, *, authorized: bool) -> None:
        if not authorized or self._task is not None or self._state == "TRIPPED":
            raise RuntimeError("Watchdog start denied")
        now = self._clock()
        self._last_decision = now
        self._last_confirmation = now
        self._state = "MONITORING"
        self._reason = ""
        self._stop_confirmed = None
        self._task = asyncio.create_task(self._monitor())

    def feed_decision(self) -> None:
        if self._state != "MONITORING":
            raise RuntimeError("Watchdog not monitoring")
        self._last_decision = self._clock()

    def feed_confirmation(self, *, verified: bool) -> None:
        if self._state != "MONITORING":
            raise RuntimeError("Watchdog not monitoring")
        if not verified:
            self._request_trip("HTTP_CONFIRMATION_FAILED")
            return
        self._last_confirmation = self._clock()

    def _request_trip(self, reason: str) -> None:
        if self._state == "MONITORING":
            self._state = "STOPPING"
            self._reason = reason
            asyncio.create_task(self._trip(reason))

    async def _trip(self, reason: str) -> None:
        async with self._trip_lock:
            if self._state == "TRIPPED":
                return
            self._state = "STOPPING"
            self._reason = reason
            try:
                result = await self._stop_callback(reason)
                self._stop_confirmed = bool(getattr(result, "zero_verified", False))
            except BaseException:
                self._stop_confirmed = False
            self._state = "TRIPPED"

    async def _monitor(self) -> None:
        try:
            while self._state == "MONITORING":
                await asyncio.sleep(self._poll_interval)
                now = self._clock()
                if self._last_decision is None or now - self._last_decision > self._decision_timeout:
                    await self._trip("EMS_DECISION_STALE")
                    return
                if self._last_confirmation is None or now - self._last_confirmation > self._confirmation_timeout:
                    await self._trip("HTTP_CONFIRMATION_STALE")
                    return
        except asyncio.CancelledError:
            # Cancellation is an unsafe exit while monitoring.
            if self._state == "MONITORING":
                await self._trip("WATCHDOG_CANCELLED")
            raise

    async def close(self) -> None:
        """Stop monitoring and request a verified zero before returning."""
        if self._state in ("MONITORING", "STOPPING"):
            await self._trip("SESSION_CLOSED")
        task = self._task
        if task is not None and task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._task = None
