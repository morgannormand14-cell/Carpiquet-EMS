"""R25 unified SolarFlow dynamic session (not connected to live coordinator).

A session owns exactly one HTTP executor and one watchdog. This is a
development-stage component: no Home Assistant UI can arm it yet.
"""
from __future__ import annotations

import asyncio

from .dynamic_http_executor import DynamicHttpExecutor
from .dynamic_watchdog import DynamicWatchdog


class DynamicControlSession:
    def __init__(self, executor: DynamicHttpExecutor, *,
                 decision_timeout_s: float = 30.0,
                 confirmation_timeout_s: float = 30.0):
        self.executor = executor
        self._lock = asyncio.Lock()
        self._watchdog = DynamicWatchdog(
            stop_callback=self._watchdog_stop,
            decision_timeout_s=decision_timeout_s,
            confirmation_timeout_s=confirmation_timeout_s,
        )
        self._closed = False
        self._closing_lock = asyncio.Lock()

    @property
    def status(self):
        return self._watchdog.status

    async def _watchdog_stop(self, reason: str):
        # The HTTP executor serializes this stop with any in-flight POST/GET.
        return await self.executor.stop(reason=reason)

    def start(self, *, authorized: bool):
        if self._closed or not authorized:
            raise RuntimeError("Session cannot start")
        self.executor.start(authorized=True)
        try:
            self._watchdog.start(authorized=True)
        except BaseException:
            # Never leave an active executor without monitoring.
            self._closed = True
            asyncio.create_task(self.executor.stop(reason="WATCHDOG_START_FAILED"))
            raise

    async def apply(self, watts: float, *, authorized: bool, conditions_valid: bool):
        async with self._lock:
            if self._closed or self.status.state != "MONITORING":
                raise RuntimeError("Session is not monitoring")
            if not authorized or not conditions_valid:
                self._closed = True
                await self._watchdog._trip("DYNAMIC_INTERLOCK_LOST")
                raise RuntimeError("Dynamic safety interlock lost")
            self._watchdog.feed_decision()
            result = await self.executor.apply(
                watts, authorized=authorized, conditions_valid=conditions_valid,
            )
            if result.state == "APPLIED_VERIFIED":
                self._watchdog.feed_confirmation(verified=True)
            elif result.state == "STOP_ZERO_VERIFIED":
                self._closed = True
                await self._watchdog.close()
            else:
                self._watchdog.feed_confirmation(verified=False)
            return result

    async def close(self):
        # Do not hold the session apply lock while the watchdog waits for
        # the executor lock: an in-flight HTTP call must be able to finish.
        async with self._closing_lock:
            self._closed = True
            await self._watchdog.close()
