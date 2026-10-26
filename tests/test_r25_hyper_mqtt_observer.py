"""Hyper MQTT callback observer tests: local/cloud isolation, no fake confirmations."""
from pathlib import Path
import importlib.util
import sys
import types
import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
PKG = "r25_mqtt_observer_test_pkg"
sys.modules.setdefault(PKG, types.ModuleType(PKG))
sys.modules[PKG].__path__ = [str(ROOT)]
spec = importlib.util.spec_from_file_location(PKG + ".observer",
                                              ROOT / "r25_hyper_mqtt_observer.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


@pytest.mark.parametrize("route", ["LOCAL_MQTT", "CLOUD_MQTT"])
def test_publication_and_broker_ack_do_not_confirm_device_or_pack(route):
    observer = module.HyperMqttObserver()
    record = observer.on_published(route=route, message_id="42",
                                   action="request_discharge", published_at=100.0)
    assert record.publish_reported and not record.broker_accepted
    record = observer.on_broker_ack(route=route, message_id="42", accepted=True)
    assert record.broker_accepted
    assert not record.device_replied
    assert not record.telemetry_confirmed
    record = observer.on_device_reply(route=route, message_id="42",
                                      received_at=101.0, success=True)
    assert record.device_replied
    assert not record.telemetry_confirmed


def test_local_cloud_message_ids_are_isolated():
    observer = module.HyperMqttObserver()
    observer.on_published(route="LOCAL_MQTT", message_id="same",
                          action="request_discharge", published_at=1)
    observer.on_published(route="CLOUD_MQTT", message_id="same",
                          action="request_discharge", published_at=2)
    observer.on_broker_ack(route="LOCAL_MQTT", message_id="same", accepted=True)
    assert not observer.get(route="CLOUD_MQTT", message_id="same").broker_accepted


def test_unknown_and_negative_reply_fail_closed():
    observer = module.HyperMqttObserver()
    assert observer.on_device_reply(route="LOCAL_MQTT", message_id="missing",
                                    received_at=5, success=True) is None
    observer.on_published(route="LOCAL_MQTT", message_id="1",
                          action="request_discharge", published_at=10)
    reply = observer.on_device_reply(route="LOCAL_MQTT", message_id="1",
                                     received_at=11, success=False)
    assert not reply.device_replied
    assert not reply.telemetry_confirmed
    with pytest.raises(ValueError):
        observer.on_published(route="LOCAL_MQTT", message_id="1",
                              action="request_discharge", published_at=12)
    with pytest.raises(ValueError):
        observer.on_device_reply(route="LOCAL_MQTT", message_id="1",
                                  received_at=9, success=True)


def test_observer_has_no_mqtt_publish_or_connection():
    source = (ROOT / "r25_hyper_mqtt_observer.py").read_text()
    assert "import paho" not in source
    assert "mqtt.publish(" not in source
    assert "async_call(" not in source
