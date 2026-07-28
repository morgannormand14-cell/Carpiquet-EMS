from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

class SimulationSessionRecorder:
    def __init__(self, hass, version: str):
        self.hass = hass
        self.version = version
        self.session_id: str | None = None
        self.started_at: datetime | None = None
        self._samples_path: Path | None = None
        self.last_file: str | None = None
        self.sample_count = 0

    @property
    def active(self) -> bool:
        return self.session_id is not None

    def _base_dir(self) -> Path:
        path = Path(self.hass.config.path("carpiquet_ems/simulations"))
        path.mkdir(parents=True, exist_ok=True)
        return path

    def start(self, initial_state: dict[str, Any], configuration: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        self.session_id = now.strftime("SIM-%Y%m%d-%H%M%S")
        self.started_at = now
        self.sample_count = 0
        self._samples_path = self._base_dir() / f".{self.session_id}.jsonl"
        header = {
            "record_type": "header",
            "session": {
                "id": self.session_id,
                "version": self.version,
                "started_at": now.isoformat(),
            },
            "initial_state": initial_state,
            "configuration": configuration,
        }
        self._samples_path.write_text(json.dumps(header, ensure_ascii=False) + "\n", encoding="utf-8")

    def append(self, sample: dict[str, Any]) -> None:
        if not self.active or self._samples_path is None:
            return
        row = {"record_type": "sample", **sample}
        with self._samples_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.sample_count += 1

    def stop(self, summary: dict[str, Any]) -> str | None:
        if not self.active or self._samples_path is None or self.started_at is None:
            return self.last_file

        ended_at = datetime.now(timezone.utc)
        rows = self._samples_path.read_text(encoding="utf-8").splitlines()
        header = json.loads(rows[0]) if rows else {}
        samples = [json.loads(line) for line in rows[1:] if line.strip()]
        payload = {
            "session": {
                **header.get("session", {}),
                "ended_at": ended_at.isoformat(),
                "duration_seconds": round((ended_at - self.started_at).total_seconds(), 1),
                "cycles": len(samples),
            },
            "initial_state": header.get("initial_state", {}),
            "configuration": header.get("configuration", {}),
            "samples": samples,
            "summary": summary,
        }
        final_path = self._base_dir() / f"{self.session_id}.json"
        final_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._samples_path.unlink(missing_ok=True)

        self.last_file = str(final_path)
        self.session_id = None
        self.started_at = None
        self._samples_path = None
        self.sample_count = 0
        return self.last_file
