from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

BINARY_SENSORS = [
    ("controlled_transport_bridge_call_requested", "Controlled Transport Bridge Call Requested", ATTR_TRANSPORT_BRIDGE_CALL_REQUESTED),
    ("controlled_transport_bridge_call_allowed", "Controlled Transport Bridge Call Allowed", ATTR_TRANSPORT_BRIDGE_CALL_ALLOWED),
    ("controlled_transport_bridge_call_sent", "Controlled Transport Bridge Call Sent", ATTR_TRANSPORT_BRIDGE_CALL_SENT),
    ("controlled_transport_bridge_verification_requested", "Controlled Transport Bridge Verification Requested", ATTR_TRANSPORT_BRIDGE_VERIFY_REQUESTED),
    ("controlled_transport_bridge_zero_return_selected", "Controlled Transport Bridge Zero Return Selected", ATTR_TRANSPORT_BRIDGE_ZERO_SELECTED),
    ("controlled_transport_bridge_write_locked", "Controlled Transport Bridge Write Locked", ATTR_TRANSPORT_BRIDGE_WRITE_LOCKED),

    ("controlled_execution_orchestrator_test_post_requested", "Controlled Execution Orchestrator Test POST Requested", ATTR_EXEC_ORCH_TEST_POST_REQUESTED),
    ("controlled_execution_orchestrator_test_post_allowed", "Controlled Execution Orchestrator Test POST Allowed", ATTR_EXEC_ORCH_TEST_POST_ALLOWED),
    ("controlled_execution_orchestrator_test_post_sent", "Controlled Execution Orchestrator Test POST Sent", ATTR_EXEC_ORCH_TEST_POST_SENT),
    ("controlled_execution_orchestrator_report_verification_requested", "Controlled Execution Orchestrator Report Verification Requested", ATTR_EXEC_ORCH_REPORT_VERIFY_REQUESTED),
    ("controlled_execution_orchestrator_wait_requested", "Controlled Execution Orchestrator Wait Requested", ATTR_EXEC_ORCH_WAIT_REQUESTED),
    ("controlled_execution_orchestrator_zero_post_requested", "Controlled Execution Orchestrator Zero POST Requested", ATTR_EXEC_ORCH_ZERO_POST_REQUESTED),
    ("controlled_execution_orchestrator_zero_post_allowed", "Controlled Execution Orchestrator Zero POST Allowed", ATTR_EXEC_ORCH_ZERO_POST_ALLOWED),
    ("controlled_execution_orchestrator_zero_post_sent", "Controlled Execution Orchestrator Zero POST Sent", ATTR_EXEC_ORCH_ZERO_POST_SENT),
    ("controlled_execution_orchestrator_zero_verification_requested", "Controlled Execution Orchestrator Zero Verification Requested", ATTR_EXEC_ORCH_ZERO_VERIFY_REQUESTED),
    ("controlled_execution_orchestrator_relock_required", "Controlled Execution Orchestrator Relock Required", ATTR_EXEC_ORCH_RELOCK_REQUIRED),
    ("controlled_execution_orchestrator_execution_allowed", "Controlled Execution Orchestrator Execution Allowed", ATTR_EXEC_ORCH_EXECUTION_ALLOWED),
    ("controlled_execution_orchestrator_command_sent", "Controlled Execution Orchestrator Command Sent", ATTR_EXEC_ORCH_COMMAND_SENT),

    ("controlled_execution_safety_execution_allowed", "Controlled Execution Safety Execution Allowed", ATTR_EXEC_SAFETY_EXECUTION_ALLOWED),
    ("controlled_execution_safety_command_sent", "Controlled Execution Safety Command Sent", ATTR_EXEC_SAFETY_COMMAND_SENT),
    ("controlled_execution_safety_single_device_only", "Controlled Execution Safety Single Device Only", ATTR_EXEC_SAFETY_SINGLE_DEVICE_ONLY),
    ("controlled_execution_safety_local_http_only", "Controlled Execution Safety Local HTTP Only", ATTR_EXEC_SAFETY_LOCAL_HTTP_ONLY),
    ("controlled_execution_safety_watchdog_required", "Controlled Execution Safety Watchdog Required", ATTR_EXEC_SAFETY_WATCHDOG_REQUIRED),
    ("controlled_execution_safety_verification_required", "Controlled Execution Safety Verification Required", ATTR_EXEC_SAFETY_VERIFICATION_REQUIRED),
    ("controlled_execution_safety_zero_return_required", "Controlled Execution Safety Zero Return Required", ATTR_EXEC_SAFETY_ZERO_RETURN_REQUIRED),
    ("controlled_execution_safety_zero_on_failure_required", "Controlled Execution Safety Zero On Failure Required", ATTR_EXEC_SAFETY_ZERO_ON_FAILURE_REQUIRED),
    ("controlled_execution_safety_relock_required", "Controlled Execution Safety Relock Required", ATTR_EXEC_SAFETY_RELOCK_REQUIRED),

    ("controlled_test_gate_armed", "Controlled Test Gate Armed", ATTR_TEST_GATE_ARMED),
    ("controlled_test_gate_execute_allowed", "Controlled Test Gate Execute Allowed", ATTR_TEST_GATE_EXECUTE_ALLOWED),
    ("controlled_test_gate_command_sent", "Controlled Test Gate Command Sent", ATTR_TEST_GATE_COMMAND_SENT),
    ("controlled_test_gate_return_to_zero", "Controlled Test Gate Return To Zero Required", ATTR_TEST_GATE_RETURN_TO_ZERO),
    ("controlled_executor_write_locked", "Controlled Executor Write Locked", ATTR_EXECUTOR_WRITE_LOCKED),
    ("controlled_executor_execution_requested", "Controlled Executor Execution Requested", ATTR_EXECUTOR_EXECUTION_REQUESTED),
    ("controlled_executor_execution_allowed", "Controlled Executor Execution Allowed", ATTR_EXECUTOR_EXECUTION_ALLOWED),
    ("controlled_executor_command_sent", "Controlled Executor Command Sent", ATTR_EXECUTOR_COMMAND_SENT),
    ("controlled_executor_hyper_prepared", "Controlled Executor Hyper Prepared", ATTR_EXECUTOR_HYPER_PREPARED),
    ("controlled_executor_solarflow_prepared", "Controlled Executor SolarFlow Prepared", ATTR_EXECUTOR_SOLARFLOW_PREPARED),
    ("controlled_executor_solarflow_post_status_required", "Controlled Executor SolarFlow POST Status Required", ATTR_EXECUTOR_SOLARFLOW_POST_STATUS_REQUIRED),
    ("controlled_executor_solarflow_report_confirmation_required", "Controlled Executor SolarFlow Report Confirmation Required", ATTR_EXECUTOR_SOLARFLOW_REPORT_CONFIRM_REQUIRED),
    ("transport_hyper_metadata_ready", "Transport Hyper Metadata Ready", ATTR_TRANSPORT_HYPER_METADATA_READY),
    ("transport_hyper_execution_ready", "Transport Hyper Execution Ready", ATTR_TRANSPORT_HYPER_EXECUTION_READY),
    ("transport_solarflow_metadata_ready", "Transport SolarFlow Metadata Ready", ATTR_TRANSPORT_SOLARFLOW_METADATA_READY),
    ("transport_solarflow_execution_ready", "Transport SolarFlow Execution Ready", ATTR_TRANSPORT_SOLARFLOW_EXECUTION_READY),
    ("solarflow_local_http_reachable", "SolarFlow Local HTTP Reachable", ATTR_SOLARFLOW_LOCAL_HTTP_REACHABLE),
    ("solarflow_local_http_qualified", "SolarFlow Local HTTP Qualified", ATTR_SOLARFLOW_LOCAL_HTTP_QUALIFIED),
    ("write_gate_execute_allowed", "Write Gate Execute Allowed", ATTR_WRITE_GATE_EXECUTE_ALLOWED),
    ("write_gate_master_lock", "Write Gate Master Lock", ATTR_WRITE_GATE_MASTER_LOCK),
    ("generic_authority", "Generic Authority", ATTR_GENERIC_AUTHORITY),
    ("real_writes_enabled", "Real Writes Enabled", ATTR_REAL_WRITES_ENABLED),
    ("mapper_ready", "Mapper Ready", ATTR_MAPPER_READY),
    ("command_adapter_write_locked", "Command Adapter Write Locked", ATTR_ADAPTER_WRITE_LOCKED),
    ("adapter_hyper_would_execute", "Adapter Hyper Would Execute", ATTR_ADAPTER_HYPER_WOULD_EXECUTE),
    ("adapter_solarflow_would_execute", "Adapter SolarFlow Would Execute", ATTR_ADAPTER_SOLARFLOW_WOULD_EXECUTE),
    ("shadow_authorized", "Shadow Authorized", ATTR_SHADOW_AUTHORIZED),
    ("raw_command_safety_ok", "Raw Command Safety OK", ATTR_RAW_COMMAND_SAFETY_OK),
    ("command_write_locked", "Command Write Locked", ATTR_COMMAND_WRITE_LOCKED),
    ("command_safety_ok", "Command Safety OK", ATTR_COMMAND_SAFETY_OK),
    ("command_safety_limited", "Command Safety Limited", ATTR_COMMAND_SAFETY_LIMITED),
    ("grid_source_fresh", "Grid Source Fresh", ATTR_GRID_SOURCE_FRESH),
    ("would_send_command", "Would Send Command", ATTR_WOULD_SEND_COMMAND),
    ("engine_initialization_ready", "Engine Initialization Ready", ATTR_ENGINE_INITIALIZATION_READY),
    ("simulation_session_finalizing", "Simulation Session Finalizing", ATTR_SESSION_FINALIZING),
    ("grid_export_allowed", "Grid Export Allowed", ATTR_GRID_EXPORT_ALLOWED),
    ("automation_safety_gate", "Automation Safety Gate", ATTR_AUTOMATION_SAFETY_OK),
    ("grid_meter_health", "Grid Meter Health", ATTR_GRID_METER_AVAILABLE),
    ("hyper_2000_health", "Hyper 2000 Health", ATTR_HYPER_AVAILABLE),
    ("solarflow_2400_pro_health", "SolarFlow 2400 Pro Health", ATTR_SOLARFLOW_AVAILABLE),
    ("simulation_session_active", "Simulation Session Active", ATTR_SESSION_ACTIVE),
]

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CarpiquetBinarySensor(coordinator, entry, *item) for item in BINARY_SENSORS])

class CarpiquetBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, key, name, data_key):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = f"Carpiquet EMS {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self._data_key, False))

    @property
    def extra_state_attributes(self):
        if self._data_key == ATTR_WRITE_GATE_MASTER_LOCK:
            return {
                "gate_state": self.coordinator.data.get(ATTR_WRITE_GATE_STATE),
                "execute_allowed": self.coordinator.data.get(ATTR_WRITE_GATE_EXECUTE_ALLOWED),
                "blockers": self.coordinator.data.get(ATTR_WRITE_GATE_BLOCKERS),
                "evaluated_at": self.coordinator.data.get(ATTR_WRITE_GATE_EVALUATED_AT),
                "version": VERSION,
            }
        return {"version": VERSION}
