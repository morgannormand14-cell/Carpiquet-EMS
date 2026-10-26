"""Read-only Hyper 2000 MQTT event observer; no broker connections or writes.

Events must originate from a trusted, explicitly wired transport callback.
A broker PUBACK does not mean the device executed the command.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

ROUTES = frozenset(("LOCAL_MQTT", "CLOUD_MQTT"))


@dataclass(frozen=True)
class MqttCommandObservation:
    route: str
    message_id: str
    action: str
    published_at: float
    publish_reported: bool = True
    broker_accepted: bool = False
    device_replied: bool = False
    telemetry_confirmed: bool = False
    reply_at: float | None = None


class HyperMqttObserver:
    """Per-session correlation store, populated only by external callbacks."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], MqttCommandObservation] = {}

    def on_published(self, *, route: str, message_id: str, action: str,
                     published_at: float) -> MqttCommandObservation:
        if route not in ROUTES:
            raise ValueError("Unsupported MQTT route")
        if not isinstance(message_id, str) or not message_id.strip():
            raise ValueError("Missing MQTT messageId")
        if not isfinite(float(published_at)):
            raise ValueError("Invalid publish timestamp")
        key = (route, message_id)
        if key in self._records:
            raise ValueError("Duplicate MQTT messageId for route")
        record = MqttCommandObservation(route, message_id, action, float(published_at))
        self._records[key] = record
        return record

    def on_broker_ack(self, *, route: str, message_id: str,
                      accepted: bool) -> MqttCommandObservation | None:
        key = (route, message_id)
        record = self._records.get(key)
        if record is None:
            return None
        # Never downgrade a previously observed acknowledgement.
        updated = replace(record, broker_accepted=record.broker_accepted or bool(accepted))
        self._records[key] = updated
        return updated

    def on_device_reply(self, *, route: str, message_id: str,
                        received_at: float, success: bool) -> MqttCommandObservation | None:
        record = self._records.get((route, message_id))
        if record is None:
            return None
        if not isfinite(float(received_at)) or float(received_at) < record.published_at:
            raise ValueError("Invalid reply timestamp")
        # A negative device reply must not be represented as success.
        updated = replace(record, device_replied=record.device_replied or bool(success),
                          reply_at=float(received_at))
        self._records[(route, message_id)] = updated
        return updated

    def get(self, *, route: str, message_id: str) -> MqttCommandObservation | None:
        return self._records.get((route, message_id))
