"""R25 concurrency and stop tests with mocked executor, no hardware access."""
import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "carpiquet_ems"
pkg = types.ModuleType("r25_test_package")
pkg.__path__ = [str(ROOT)]
sys.modules.setdefault("r25_test_package", pkg)


def load(name):
    spec = importlib.util.spec_from_file_location(f"r25_test_package.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# The session imports DynamicHttpExecutor only for typing; mock its module.
http_stub = types.ModuleType("r25_test_package.dynamic_http_executor")
http_stub.DynamicHttpExecutor = object
sys.modules[http_stub.__name__] = http_stub
load("dynamic_watchdog")
Session = load("dynamic_control_session").DynamicControlSession


class Result:
    def __init__(self, state, zero_verified=False):
        self.state = state
        self.zero_verified = zero_verified


class FakeExecutor:
    def __init__(self):
        self.active = False
        self.calls = []
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self._lock = asyncio.Lock()

    def start(self, *, authorized):
        assert authorized
        self.active = True

    async def apply(self, watts, *, authorized, conditions_valid):
        async with self._lock:
            self.calls.append(("apply", watts))
            self.entered.set()
            await self.release.wait()
            return Result("APPLIED_VERIFIED")

    async def stop(self, *, reason):
        async with self._lock:
            self.calls.append(("stop", reason))
            self.active = False
            return Result("STOP_ZERO_VERIFIED", True)


@pytest.mark.asyncio
async def test_close_waits_for_inflight_command_then_zero():
    executor = FakeExecutor()
    session = Session(executor)
    session.start(authorized=True)
    apply_task = asyncio.create_task(session.apply(300, authorized=True, conditions_valid=True))
    await executor.entered.wait()
    close_task = asyncio.create_task(session.close())
    await asyncio.sleep(0)
    assert not close_task.done()
    executor.release.set()
    await asyncio.wait_for(asyncio.gather(apply_task, close_task), 2)
    assert executor.calls[0] == ("apply", 300)
    assert executor.calls[-1][0] == "stop"
    assert session.status.stop_confirmed is True


@pytest.mark.asyncio
async def test_double_close_sends_only_one_zero():
    executor = FakeExecutor()
    session = Session(executor)
    session.start(authorized=True)
    await asyncio.wait_for(asyncio.gather(session.close(), session.close()), 2)
    assert sum(1 for name, _ in executor.calls if name == "stop") == 1


@pytest.mark.asyncio
async def test_interlock_loss_stops_without_deadlock():
    executor = FakeExecutor()
    session = Session(executor)
    session.start(authorized=True)
    with pytest.raises(RuntimeError, match="interlock"):
        await asyncio.wait_for(
            session.apply(300, authorized=False, conditions_valid=False), 2
        )
    assert session.status.stop_confirmed is True
    await session.close()


@pytest.mark.asyncio
async def test_late_confirmation_does_not_rearm_after_close():
    executor = FakeExecutor()
    session = Session(executor)
    session.start(authorized=True)
    pending = asyncio.create_task(
        session.apply(450, authorized=True, conditions_valid=True)
    )
    await executor.entered.wait()
    stopping = asyncio.create_task(session.close())
    await asyncio.sleep(0)
    executor.release.set()
    await asyncio.wait_for(asyncio.gather(pending, stopping), 2)
    assert session.status.state == "TRIPPED"
    assert session.status.stop_confirmed is True
    with pytest.raises(RuntimeError, match="not monitoring"):
        await session.apply(450, authorized=True, conditions_valid=True)
    assert sum(1 for name, _ in executor.calls if name == "stop") == 1


@pytest.mark.asyncio
async def test_watchdog_trip_during_inflight_command_requests_zero():
    executor = FakeExecutor()
    session = Session(executor)
    session.start(authorized=True)
    pending = asyncio.create_task(session.apply(250, authorized=True, conditions_valid=True))
    await executor.entered.wait()
    tripping = asyncio.create_task(session._watchdog._trip("EMS_DECISION_STALE"))
    await asyncio.sleep(0)
    executor.release.set()
    await asyncio.wait_for(asyncio.gather(pending, tripping), 2)
    assert session.status.state == "TRIPPED"
    assert session.status.stop_confirmed is True
    assert executor.calls[-1][0] == "stop"
    await session.close()


@pytest.mark.asyncio
async def test_repeated_close_during_pending_command_is_serialized():
    executor = FakeExecutor()
    session = Session(executor)
    session.start(authorized=True)
    pending = asyncio.create_task(session.apply(200, authorized=True, conditions_valid=True))
    await executor.entered.wait()
    closing = [asyncio.create_task(session.close()) for _ in range(3)]
    await asyncio.sleep(0)
    executor.release.set()
    await asyncio.wait_for(asyncio.gather(pending, *closing), 2)
    assert sum(1 for name, _ in executor.calls if name == "stop") == 1
    assert session.status.stop_confirmed is True
