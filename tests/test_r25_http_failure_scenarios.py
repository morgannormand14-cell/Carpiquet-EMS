"""R25 simulated HTTP failure and physical-zero verification tests."""
import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
PKG = "r25_http_safety"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules.setdefault(PKG, package)

def load(name):
    spec = importlib.util.spec_from_file_location(f"{PKG}.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

helper = types.ModuleType(f"{PKG}.controlled_real_test_executor")
helper._post = None
helper._get_output = None
helper._restore_zero = None
sys.modules[helper.__name__] = helper
http = load("dynamic_http_executor")

ha = types.ModuleType("homeassistant")
ha.__path__ = []
helpers = types.ModuleType("homeassistant.helpers")
helpers.__path__ = []
client = types.ModuleType("homeassistant.helpers.aiohttp_client")
client.async_get_clientsession = lambda hass: object()
sys.modules.update({"homeassistant": ha, "homeassistant.helpers": helpers,
                    "homeassistant.helpers.aiohttp_client": client})

def executor():
    x = http.DynamicHttpExecutor(
        object(), write_target="http://local/properties/write",
        report_target="http://local/properties/report",
        envelope={"id": "test", "sn": "test", "properties": {"outputLimit": 0}},
        limit_w=1000,
    )
    x.start(authorized=True)
    return x

@pytest.mark.asyncio
@pytest.mark.parametrize("failed_operation", ["POST", "GET"])
async def test_network_failure_requests_zero(monkeypatch, failed_operation):
    async def post(session, target, body):
        if failed_operation == "POST":
            raise TimeoutError("simulated POST timeout")
        return 200
    async def get(session, target):
        if failed_operation == "GET":
            raise TimeoutError("simulated GET timeout")
        return 200, 300.0
    zero_calls = []
    async def zero(session, target, report, body):
        zero_calls.append(body["properties"]["outputLimit"])
        return 200, True, ""
    monkeypatch.setattr(http, "_post", post)
    monkeypatch.setattr(http, "_get_output", get)
    monkeypatch.setattr(http, "_restore_zero", zero)
    monkeypatch.setattr(http.asyncio, "sleep", fast_sleep)
    x = executor()
    result = await x.apply(300, authorized=True, conditions_valid=True)
    assert result.state == "FAULT_ZERO_VERIFIED"
    assert result.zero_verified is True
    assert zero_calls == [0.0]
    assert x.fault is True and x.active is False

async def fast_sleep(seconds):
    return None

@pytest.mark.asyncio
async def test_zero_unconfirmed_is_latched_fault(monkeypatch):
    async def post(session, target, body):
        raise TimeoutError("lost connection")
    async def zero(session, target, report, body):
        return None, False, "ZERO_READBACK_UNCONFIRMED"
    monkeypatch.setattr(http, "_post", post)
    monkeypatch.setattr(http, "_restore_zero", zero)
    x = executor()
    result = await x.apply(300, authorized=True, conditions_valid=True)
    assert result.state == "FAULT_ZERO_UNCONFIRMED"
    assert result.zero_verified is False
    assert x.fault is True
    with pytest.raises(RuntimeError, match="locked"):
        await x.apply(200, authorized=True, conditions_valid=True)

@pytest.mark.asyncio
async def test_normal_stop_verifies_zero(monkeypatch):
    calls = []
    async def zero(session, target, report, body):
        calls.append(body["properties"]["outputLimit"])
        return 200, True, ""
    monkeypatch.setattr(http, "_restore_zero", zero)
    x = executor()
    result = await x.stop(reason="OPERATOR_SIMULATION")
    assert result.state == "STOP_ZERO_VERIFIED"
    assert result.zero_verified and calls == [0.0]
    assert x.active is False
