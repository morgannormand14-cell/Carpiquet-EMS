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
        p = Path(self.hass.config.path("carpiquet_ems/simulations"))
        p.mkdir(parents=True, exist_ok=True)
        return p

    def list_reports(self) -> list[str]:
        return sorted((p.name for p in self._base_dir().glob("SIM-*.json")), reverse=True)

    def start(self, initial_state: dict[str, Any], configuration: dict[str, Any]) -> None:
        if self.active:
            return
        now = datetime.now(timezone.utc)
        self.session_id = now.strftime("SIM-%Y%m%d-%H%M%S")
        self.started_at = now
        self.sample_count = 0
        self._samples_path = self._base_dir() / f".{self.session_id}.jsonl"
        header = {
            "record_type": "header",
            "session": {"id": self.session_id, "version": self.version, "started_at": now.isoformat()},
            "initial_state": initial_state,
            "configuration": configuration,
        }
        self._samples_path.write_text(json.dumps(header, ensure_ascii=False)+"\n", encoding="utf-8")

    def append(self, sample: dict[str, Any]) -> None:
        if not self.active or self._samples_path is None:
            return
        with self._samples_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"record_type":"sample", **sample}, ensure_ascii=False)+"\n")
        self.sample_count += 1

    def stop(self, summary: dict[str, Any], termination: str = "user_stop") -> str | None:
        if not self.active or self._samples_path is None or self.started_at is None:
            return self.last_file
        ended = datetime.now(timezone.utc)
        rows = self._samples_path.read_text(encoding="utf-8").splitlines()
        header = json.loads(rows[0]) if rows else {}
        samples = [json.loads(x) for x in rows[1:] if x.strip()]
        payload = {
            "session": {
                **header.get("session", {}),
                "ended_at": ended.isoformat(),
                "duration_seconds": round((ended-self.started_at).total_seconds(),1),
                "cycles": len(samples),
                "termination": termination,
            },
            "initial_state": header.get("initial_state", {}),
            "configuration": header.get("configuration", {}),
            "samples": samples,
            "summary": summary,
        }
        final = self._base_dir()/f"{self.session_id}.json"
        final.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._samples_path.unlink(missing_ok=True)
        self.last_file = str(final)
        self.session_id = None
        self.started_at = None
        self._samples_path = None
        self.sample_count = 0
        return self.last_file

    def finalize_orphaned_sessions(self) -> None:
        # Preserve interrupted sessions instead of silently losing them.
        for temp in self._base_dir().glob(".SIM-*.jsonl"):
            try:
                rows = temp.read_text(encoding="utf-8").splitlines()
                if not rows:
                    temp.unlink(missing_ok=True)
                    continue
                header = json.loads(rows[0])
                samples = [json.loads(x) for x in rows[1:] if x.strip()]
                sid = header.get("session",{}).get("id") or temp.stem.lstrip(".")
                final = self._base_dir()/f"{sid}.json"
                if not final.exists():
                    payload = {
                        "session": {
                            **header.get("session",{}),
                            "ended_at": datetime.now(timezone.utc).isoformat(),
                            "cycles": len(samples),
                            "termination": "home_assistant_interruption",
                        },
                        "initial_state": header.get("initial_state",{}),
                        "configuration": header.get("configuration",{}),
                        "samples": samples,
                        "summary": {"status":"session interrompue"},
                    }
                    final.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
                temp.unlink(missing_ok=True)
            except Exception:
                # Never prevent integration startup because of one damaged old report.
                continue
