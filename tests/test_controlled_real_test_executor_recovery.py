"""Regression tests for bounded SolarFlow zero recovery (no hardware I/O)."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
from unittest.mock import patch

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems/controlled_real_test_executor.py"
spec = importlib.util.spec_from_file_location("controlled_real_test_executor_under_test", MODULE_PATH)
executor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = executor
spec.loader.exec_module(executor)


class Response:
    def __init__(self, status, power=None):
        self.status = status
        self.power = power

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def read(self):
        return b""

    async def json(self, content_type=None):
        return {"properties": {"outputLimit": self.power}}


class Session:
    def __init__(self, posts, reads):
        self.posts = iter(posts)
        self.reads = iter(reads)
        self.bodies = []

    def post(self, target, json, timeout):
        self.bodies.append(json["properties"]["outputLimit"])
        item = next(self.posts)
        if isinstance(item, Exception):
            raise item
        return Response(item)

    def get(self, target, timeout):
        item = next(self.reads)
        if isinstance(item, Exception):
            raise item
        return Response(*item)


def fake_ha_session(session):
    ha = types.ModuleType("homeassistant")
    helpers = types.ModuleType("homeassistant.helpers")
    client = types.ModuleType("homeassistant.helpers.aiohttp_client")
    client.async_get_clientsession = lambda hass: session
    return patch.dict(sys.modules, {
        "homeassistant": ha,
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.aiohttp_client": client,
    })


async def fast_sleep(seconds):
    return None


async def run(session):
    with fake_ha_session(session), patch.object(executor.asyncio, "sleep", fast_sleep):
        return await executor.execute_single_solarflow_test(
            None,
            test_target="http://solarflow/properties/write",
            report_target="http://solarflow/properties/report",
            test_body={"properties": {"outputLimit": 100}},
            zero_body={"properties": {"outputLimit": 0}},
            power_w=100,
            duration_seconds=0,
        )


@pytest.mark.asyncio
async def test_successful_test_and_zero():
    session = Session([200, 200], [(200, 100), (200, 0)])
    result = await run(session)
    assert result.state == "REAL_TEST_COMPLETE_RELOCKED"
    assert result.zero_verified is True
    assert session.bodies == [100, 0]


@pytest.mark.asyncio
async def test_timed_out_initial_post_still_zeroes():
    session = Session([TimeoutError("lost reply"), 200], [(200, 0)])
    result = await run(session)
    assert result.test_verified is False
    assert result.zero_verified is True
    assert session.bodies == [100, 0]


@pytest.mark.asyncio
async def test_failed_zero_is_not_reported_as_verified():
    session = Session([200, 500, 500, 500], [(200, 100), (200, 100), (200, 100), (200, 100)])
    result = await run(session)
    assert result.state == "ZERO_UNCONFIRMED_RELOCKED"
    assert result.relocked is True
    assert result.zero_verified is False
    assert session.bodies == [100, 0, 0, 0]


@pytest.mark.asyncio
async def test_lost_zero_response_can_still_verify_readback():
    session = Session([200, TimeoutError("reply lost")], [(200, 100), (200, 0)])
    result = await run(session)
    assert result.zero_verified is True
    assert session.bodies == [100, 0]


@pytest.mark.asyncio
async def test_failed_test_readback_still_zeroes():
    session = Session([200, 200], [(200, 75), (200, 0)])
    result = await run(session)
    assert result.test_verified is False
    assert result.zero_verified is True
    assert session.bodies == [100, 0]
