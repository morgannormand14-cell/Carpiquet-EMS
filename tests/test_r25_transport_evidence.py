"""R25 transport evidence contract tests; no Home Assistant or device I/O."""
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components/carpiquet_ems"
PKG = "r25_evidence_test_pkg"
package = types.ModuleType(PKG)
package.__path__ = [str(ROOT)]
sys.modules[PKG] = package


def load(name):
    spec = importlib.util.spec_from_file_location(f"{PKG}.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load("transition_feedback")
load("transition_confirmation_tracker")
load("r25_command_correlation")
m = load("r25_transport_evidence")


def test_prepared_mqtt_and_zensdk_never_count_as_dispatched():
    for system, transport in (
        ("hyper_2000", "LOCAL_MQTT"),
        ("hyper_2000", "CLOUD_MQTT"),
        ("solarflow_2400_pro", "ZenSDK"),
    ):
        evidence = m.unproven_transport_evidence(
            system_id=system, transport=transport, action="request_discharge",
        )
        assert evidence.dispatched is False
        result = m.correlate_evidence(
            evidence, now=105, telemetry_at=104, observed_state="discharging",
            observed_soc=80, minimum_soc=10,
        )
        assert result.state == "NOT_TRACKED"
        assert not result.confirmed


def test_acknowledgement_without_new_telemetry_is_not_confirmation():
    evidence = m.dispatched_transport_evidence(
        system_id="hyper_2000", transport="LOCAL_MQTT",
        action="request_discharge", command_id="test-1", sent_at=100, accepted=True,
    )
    result = m.correlate_evidence(
        evidence, now=105, telemetry_at=99, observed_state="discharging",
        observed_soc=80, minimum_soc=10,
    )
    assert not result.confirmed
    assert result.state == "PENDING"


def test_confirm_only_after_fresh_matching_pack_telemetry():
    evidence = m.dispatched_transport_evidence(
        system_id="hyper_2000", transport="CLOUD_MQTT",
        action="request_discharge", command_id="test-2", sent_at=100, accepted=True,
    )
    result = m.correlate_evidence(
        evidence, now=105, telemetry_at=104, observed_state="discharging",
        observed_soc=80, minimum_soc=10,
    )
    assert result.confirmed
    assert result.command_id == "test-2"


def test_zensdk_transport_ack_cannot_replace_pack_transition():
    evidence = m.dispatched_transport_evidence(
        system_id="solarflow_2400_pro", transport="ZenSDK",
        action="request_discharge", command_id="test-3", sent_at=100, accepted=True,
    )
    result = m.correlate_evidence(
        evidence, now=105, telemetry_at=104, observed_state="standby",
        observed_soc=80, minimum_soc=10,
    )
    assert not result.confirmed


def test_invalid_dispatch_identity_fails_closed():
    for command_id in ("", None):
        try:
            m.dispatched_transport_evidence(
                system_id="hyper_2000", transport="LOCAL_MQTT",
                action="request_discharge", command_id=command_id,
                sent_at=100, accepted=True,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid command identifier accepted")
