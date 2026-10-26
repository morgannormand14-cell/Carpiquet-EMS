"""R25 Hyper MQTT event contract: local/cloud remain unproven without publisher."""
from pathlib import Path
import ast
import importlib.util
import sys
import types
import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
PACKAGE = "r25_mqtt_event_test_pkg"
sys.modules.setdefault(PACKAGE, types.ModuleType(PACKAGE))
sys.modules[PACKAGE].__path__ = [str(ROOT)]
spec = importlib.util.spec_from_file_location(PACKAGE + ".r25_hyper_mqtt_events",
                                              ROOT / "r25_hyper_mqtt_events.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


@pytest.mark.parametrize("route", ["LOCAL_MQTT", "CLOUD_MQTT"])
def test_preparation_does_not_prove_publish(route):
    event = module.unproven_hyper_mqtt_event(transport=route, action="request_discharge")
    assert event.command_id is None
    assert not event.published
    assert event.published_at is None
    assert not event.broker_accepted
    assert not event.device_acknowledged
    assert not event.pack_transition_confirmed


@pytest.mark.parametrize("route", ["LOCAL_MQTT", "CLOUD_MQTT"])
def test_real_transport_callback_only_records_broker_ack(route):
    event = module.observed_hyper_mqtt_publish(
        transport=route, action="request_discharge",
        command_id="mqtt-123", published_at=123.5, broker_accepted=True)
    assert event.published and event.broker_accepted
    assert not event.device_acknowledged
    assert not event.pack_transition_confirmed


def test_invalid_route_or_timestamp_rejected():
    with pytest.raises(ValueError):
        module.observed_hyper_mqtt_publish(transport="UNKNOWN", action="request_discharge",
                                           command_id="1", published_at=1, broker_accepted=True)
    with pytest.raises(ValueError):
        module.observed_hyper_mqtt_publish(transport="LOCAL_MQTT", action="request_discharge",
                                           command_id="1", published_at=float("nan"),
                                           broker_accepted=True)


def test_coordinator_diagnostic_is_read_only():
    source = (ROOT / "coordinator.py").read_text()
    ast.parse(source)
    assert "self._r25_hyper_mqtt_event = unproven_hyper_mqtt_event(" in source
    assert '"r25_hyper_mqtt_event": {' in source
    assert '"pack_transition_confirmed": False' in source
