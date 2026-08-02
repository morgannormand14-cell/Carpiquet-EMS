from pathlib import Path
import json
import threading
import time

from custom_components.carpiquet_ems.session_recorder import SimulationSessionRecorder


class Config:
    def __init__(self, root):
        self.root = Path(root)
    def path(self, relative):
        return str(self.root / relative)


class Hass:
    def __init__(self, root):
        self.config = Config(root)


def test_stop_is_atomic_and_rejects_late_samples(tmp_path):
    recorder = SimulationSessionRecorder(Hass(tmp_path), "test")
    recorder.start({}, {})
    recorder.append({"timestamp": "first", "value": 1})

    original_read_text = Path.read_text
    entered = threading.Event()
    release = threading.Event()

    def delayed_read(path, *args, **kwargs):
        if path.name.endswith(".jsonl"):
            entered.set()
            release.wait(timeout=2)
        return original_read_text(path, *args, **kwargs)

    Path.read_text = delayed_read
    try:
        result = {}
        thread = threading.Thread(
            target=lambda: result.setdefault("path", recorder.stop({}, "user_stop"))
        )
        thread.start()
        entered.wait(timeout=2)
        # append waits for the stop lock and is rejected after finalization.
        late_result = {}
        append_thread = threading.Thread(
            target=lambda: late_result.setdefault(
                "accepted", recorder.append({"timestamp": "late", "value": 2})
            )
        )
        append_thread.start()
        release.set()
        thread.join(timeout=3)
        append_thread.join(timeout=3)
    finally:
        Path.read_text = original_read_text

    payload = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
    assert payload["session"]["termination"] == "user_stop"
    assert payload["session"]["cycles"] == 1
    assert payload["samples"][-1]["timestamp"] == "first"
    assert late_result["accepted"] is False
    assert not list((tmp_path / "carpiquet_ems/simulations").glob("*.tmp"))


def test_coordinator_disables_runtime_before_stop():
    source = Path("custom_components/carpiquet_ems/coordinator.py").read_text(
        encoding="utf-8"
    )
    method = source.split(
        "async def async_set_automation_enabled", 1
    )[1].split("def _session_initial_state", 1)[0]
    assert method.index("self._automation_enabled_runtime = False") < method.index(
        'await self.async_stop_simulation_session("user_stop")'
    )
    assert "not self._session_stopping" in source
