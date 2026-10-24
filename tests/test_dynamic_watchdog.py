"""R25 watchdog regression tests; simulated clock and stop, no device writes."""
import asyncio
import importlib.util
from pathlib import Path
import sys

import pytest

path = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/dynamic_watchdog.py"
spec = importlib.util.spec_from_file_location("dynamic_watchdog_under_test", path)
watchdog = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = watchdog
spec.loader.exec_module(watchdog)


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


class StopResult:
    def __init__(self, verified):
        self.zero_verified = verified


@pytest.mark.asyncio
async def test_stale_decision_trips_and_calls_stop():
    clock = Clock()
    reasons = []

    async def stop(reason):
        reasons.append(reason)
        return StopResult(True)

    w = watchdog.DynamicWatchdog(stop_callback=stop, clock=clock,
                                decision_timeout_s=5, confirmation_timeout_s=10)
    w.start(authorized=True)
    clock.now = 6
    await w._trip("EMS_DECISION_STALE")
    assert w.status.state == "TRIPPED"
    assert w.status.stop_confirmed is True
    assert reasons == ["EMS_DECISION_STALE"]
    await w.close()


@pytest.mark.asyncio
async def test_confirmation_failure_latches_unverified_zero():
    async def stop(reason):
        return StopResult(False)

    w = watchdog.DynamicWatchdog(stop_callback=stop)
    w.start(authorized=True)
    w.feed_confirmation(verified=False)
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert w.status.state == "TRIPPED"
    assert w.status.stop_confirmed is False
    await w.close()


@pytest.mark.asyncio
async def test_close_stops_active_session():
    calls = []

    async def stop(reason):
        calls.append(reason)
        return StopResult(True)

    w = watchdog.DynamicWatchdog(stop_callback=stop)
    w.start(authorized=True)
    await w.close()
    assert calls == ["SESSION_CLOSED"]
    assert w.status.stop_confirmed is True


def test_start_requires_explicit_authorization():
    async def stop(reason):
        return StopResult(True)

    w = watchdog.DynamicWatchdog(stop_callback=stop)
    with pytest.raises(RuntimeError):
        w.start(authorized=False)
