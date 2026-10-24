"""R25 dynamic HTTP executor static safety contract tests.

The dynamic transport remains disconnected from coordinator and never executes
against hardware in these tests.
"""
from pathlib import Path


def test_r25_executor_is_connected_to_coordinator():
    root = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
    coordinator = (root / "coordinator.py").read_text(encoding="utf-8")
    assert "from .dynamic_http_executor import" in coordinator
    assert "DynamicHttpExecutor(" in coordinator


def test_r25_executor_declares_required_safety_mechanisms():
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components/carpiquet_ems/dynamic_http_executor.py"
    ).read_text(encoding="utf-8")
    for required in (
        "asyncio.Lock()", "SETTLE_SECONDS = 5.0",
        "_restore_zero(", "READBACK_NOT_CONFIRMED",
        "FAULT_ZERO_UNCONFIRMED", "STOP_ZERO_UNCONFIRMED",
        "asyncio.shield(recovery)", "Dynamic session locked",
    ):
        assert required in source
