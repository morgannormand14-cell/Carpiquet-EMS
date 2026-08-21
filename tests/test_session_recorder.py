from pathlib import Path
import json
from custom_components.carpiquet_ems.session_recorder import SimulationSessionRecorder

class Config:
    def __init__(self, root): self.root = root
    def path(self, rel): return str(Path(self.root) / rel)

class Hass:
    def __init__(self, root): self.config = Config(root)

def test_session_file(tmp_path):
    recorder = SimulationSessionRecorder(Hass(tmp_path), "0.6.1-alpha-sprint6")
    recorder.start({"soc": 50}, {"grid_target": 0})
    recorder.append({"timestamp": "t1", "grid_real_w": 100})
    result = recorder.stop({"performance_score_percent": 95})
    payload = json.loads(Path(result).read_text(encoding="utf-8"))
    assert payload["session"]["cycles"] == 1
    assert payload["initial_state"]["soc"] == 50
    assert payload["summary"]["performance_score_percent"] == 95
