"""R25 simulated coordinator mode-transition/reload lifecycle checks.

Exercise actual coordinator methods with a lightweight instance, without HA or HTTP.
"""
import asyncio
import ast
from pathlib import Path
import pytest

SOURCE = (Path(__file__).resolve().parents[1] / "custom_components" /
          "carpiquet_ems" / "coordinator.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
CLASS = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and
             any(isinstance(x, ast.AsyncFunctionDef) and x.name == "async_set_r25_cycle_mode"
                 for x in n.body))
METHODS = ("async_set_r25_cycle_mode", "async_shutdown")
methods = [n for n in CLASS.body if isinstance(n, ast.AsyncFunctionDef) and n.name in METHODS]
ns = {
    "asyncio": asyncio,
    "CONTROL_MODE_SIMULATION": "Simulation",
    "datetime": __import__("datetime").datetime,
    "timezone": __import__("datetime").timezone,
    "_LOGGER": __import__("logging").getLogger("r25_test"),
}
exec(compile(ast.Module(body=methods, type_ignores=[]), "<r25-coordinator-methods>", "exec"), ns)

class Session:
    def __init__(self, zero=True):
        self.zero = zero
        self.closes = 0
        self.status = type("Status", (), {"stop_confirmed": None})()
    async def close(self):
        self.closes += 1
        await asyncio.sleep(0)
        self.status.stop_confirmed = self.zero

class Coordinator:
    async_set_r25_cycle_mode = ns["async_set_r25_cycle_mode"]
    async_shutdown = ns["async_shutdown"]
    def __init__(self):
        self._r25_transition_lock = asyncio.Lock()
        self._r25_update_lock = asyncio.Lock()
        self._r25_cycle_mode = "Simulation"
        self._r25_session = None
        self._real_test_running = False
        self._r25_ready_for_real = True
        self._r25_transport_info = {
            "target": "http://localhost/properties/write",
            "report_target": "http://localhost/properties/report",
            "envelope": {"id": "test", "sn": "test", "properties": {"outputLimit": 0}},
            "limit_w": 1000,
        }
        self.hass = object()
        self.refresh_count = 0
        self._safety_state_machine = type("Safety", (), {"reset": lambda *args: None})()
    async def async_request_refresh(self):
        self.refresh_count += 1
    async def async_stop_simulation_session(self, reason):
        return None

class FakeDynamicSession(Session):
    def __init__(self, executor):
        super().__init__()
    def start(self, *, authorized):
        assert authorized

class FakeHttpExecutor:
    def __init__(self, *args, **kwargs):
        pass

ns["DynamicHttpExecutor"] = FakeHttpExecutor
ns["DynamicControlSession"] = FakeDynamicSession

@pytest.mark.asyncio
async def test_reload_closes_real_session_without_refresh():
    c = Coordinator()
    active = Session()
    c._r25_session = active
    c._r25_cycle_mode = "Cycle réel"
    await c.async_shutdown()
    assert c._r25_cycle_mode == "Simulation"
    assert c._r25_session is None
    assert active.closes == 1
    assert active.status.stop_confirmed is True
    assert c.refresh_count == 0

@pytest.mark.asyncio
async def test_shutdown_rejects_unconfirmed_zero():
    c = Coordinator()
    c._r25_session = Session(zero=False)
    with pytest.raises(RuntimeError, match="physical zero"):
        await c.async_shutdown()
    assert c._r25_cycle_mode == "Simulation"
    assert c._r25_session is None

@pytest.mark.asyncio
async def test_rapid_simulation_real_simulation_transitions():
    c = Coordinator()
    await asyncio.wait_for(c.async_set_r25_cycle_mode(True), 2)
    assert c._r25_cycle_mode == "Cycle réel"
    previous = c._r25_session
    await asyncio.wait_for(asyncio.gather(
        c.async_set_r25_cycle_mode(False),
        c.async_set_r25_cycle_mode(True),
        c.async_set_r25_cycle_mode(False),
    ), 2)
    assert c._r25_cycle_mode == "Simulation"
    assert c._r25_session is None
    assert previous.closes == 1

@pytest.mark.asyncio
async def test_shutdown_and_mode_off_race_serialized():
    c = Coordinator()
    active = Session()
    c._r25_session = active
    c._r25_cycle_mode = "Cycle réel"
    await asyncio.wait_for(asyncio.gather(
        c.async_shutdown(), c.async_set_r25_cycle_mode(False)
    ), 2)
    assert active.closes == 1
    assert c._r25_session is None


@pytest.mark.asyncio
async def test_simulation_off_when_no_session_is_idempotent():
    c = Coordinator()
    await asyncio.wait_for(c.async_set_r25_cycle_mode(False), 2)
    assert c._r25_session is None
    assert c._r25_cycle_mode == "Simulation"


@pytest.mark.asyncio
async def test_operator_stop_waits_for_inflight_ems_update():
    c = Coordinator()
    active = Session()
    c._r25_session = active
    c._r25_cycle_mode = "Cycle réel"
    entered = asyncio.Event()
    release = asyncio.Event()

    async def ems_cycle():
        async with c._r25_update_lock:
            entered.set()
            await release.wait()

    update = asyncio.create_task(ems_cycle())
    await entered.wait()
    stopping = asyncio.create_task(c.async_set_r25_cycle_mode(False))
    await asyncio.sleep(0)
    assert not stopping.done()
    assert active.closes == 0
    release.set()
    await asyncio.wait_for(asyncio.gather(update, stopping), 2)
    assert active.closes == 1
    assert active.status.stop_confirmed is True
    assert c._r25_session is None
