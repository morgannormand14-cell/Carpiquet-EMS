from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any


class SimulationSessionRecorder:
    """Thread-safe simulation recorder with atomic finalization."""

    def __init__(self, hass, version: str):
        self.hass = hass
        self.version = version
        self.session_id: str | None = None
        self.started_at: datetime | None = None
        self._samples_path: Path | None = None
        self.last_file: str | None = None
        self.last_ended_at: str | None = None
        self.sample_count = 0
        self.finalizing = False
        self.last_error: str | None = None
        self._lock = RLock()

    @property
    def active(self) -> bool:
        with self._lock:
            return self.session_id is not None and not self.finalizing

    @property
    def recording_state(self) -> str:
        with self._lock:
            if self.finalizing:
                return "Finalisation du rapport"
            if self.session_id is not None:
                return "Enregistrement actif"
            if self.last_error:
                return "Erreur de sauvegarde"
            if self.last_file:
                return "Rapport sauvegardé"
            return "Inactif"

    def _base_dir(self) -> Path:
        p = Path(self.hass.config.path("carpiquet_ems/simulations"))
        p.mkdir(parents=True, exist_ok=True)
        return p

    def list_reports(self) -> list[str]:
        return sorted(
            (p.name for p in self._base_dir().glob("SIM-*.json")),
            reverse=True,
        )

    def start(
        self,
        initial_state: dict[str, Any],
        configuration: dict[str, Any],
    ) -> None:
        with self._lock:
            if self.session_id is not None or self.finalizing:
                return
            now = datetime.now(timezone.utc)
            self.session_id = now.strftime("SIM-%Y%m%d-%H%M%S")
            self.started_at = now
            self.sample_count = 0
            self.last_error = None
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
            self._samples_path.write_text(
                json.dumps(header, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    def append(self, sample: dict[str, Any]) -> bool:
        with self._lock:
            if (
                self.session_id is None
                or self.finalizing
                or self._samples_path is None
            ):
                return False
            with self._samples_path.open("a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps(
                        {"record_type": "sample", **sample},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                fh.flush()
            self.sample_count += 1
            return True

    def stop(
        self,
        summary: dict[str, Any],
        termination: str = "user_stop",
    ) -> str | None:
        # Lock prevents append() from crossing the finalization boundary.
        with self._lock:
            if (
                self.session_id is None
                or self._samples_path is None
                or self.started_at is None
            ):
                return self.last_file

            self.finalizing = True
            sid = self.session_id
            samples_path = self._samples_path
            started_at = self.started_at

            try:
                rows = samples_path.read_text(encoding="utf-8").splitlines()
                header = json.loads(rows[0]) if rows else {}
                samples = [json.loads(row) for row in rows[1:] if row.strip()]

                # ended_at is deliberately captured after the final accepted sample.
                ended = datetime.now(timezone.utc)
                payload = {
                    "session": {
                        **header.get("session", {}),
                        "ended_at": ended.isoformat(),
                        "duration_seconds": round(
                            (ended - started_at).total_seconds(), 1
                        ),
                        "cycles": len(samples),
                        "termination": termination,
                    },
                    "initial_state": header.get("initial_state", {}),
                    "configuration": header.get("configuration", {}),
                    "samples": samples,
                    "summary": summary,
                }

                final = self._base_dir() / f"{sid}.json"
                atomic = self._base_dir() / f".{sid}.json.tmp"
                atomic.write_text(
                    json.dumps(payload, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                os.replace(atomic, final)

                samples_path.unlink(missing_ok=True)
                self.last_file = str(final)
                self.last_ended_at = ended.isoformat()
                self.last_error = None
                return self.last_file
            except Exception as err:
                # Keep the JSONL for startup recovery.
                self.last_error = f"{type(err).__name__}: {err}"
                raise
            finally:
                self.session_id = None
                self.started_at = None
                self._samples_path = None
                self.sample_count = 0
                self.finalizing = False

    def finalize_orphaned_sessions(self) -> None:
        for temp in self._base_dir().glob(".SIM-*.jsonl"):
            try:
                rows = temp.read_text(encoding="utf-8").splitlines()
                if not rows:
                    temp.unlink(missing_ok=True)
                    continue
                header = json.loads(rows[0])
                samples = [json.loads(row) for row in rows[1:] if row.strip()]
                sid = (
                    header.get("session", {}).get("id")
                    or temp.stem.lstrip(".")
                )
                final = self._base_dir() / f"{sid}.json"
                if not final.exists():
                    ended = datetime.now(timezone.utc)
                    started_raw = header.get("session", {}).get("started_at")
                    duration = None
                    if started_raw:
                        try:
                            started = datetime.fromisoformat(started_raw)
                            duration = round((ended - started).total_seconds(), 1)
                        except (TypeError, ValueError):
                            duration = None
                    payload = {
                        "session": {
                            **header.get("session", {}),
                            "ended_at": ended.isoformat(),
                            "duration_seconds": duration,
                            "cycles": len(samples),
                            "termination": "home_assistant_interruption",
                        },
                        "initial_state": header.get("initial_state", {}),
                        "configuration": header.get("configuration", {}),
                        "samples": samples,
                        "summary": {"status": "session interrompue"},
                    }
                    atomic = self._base_dir() / f".{sid}.json.tmp"
                    atomic.write_text(
                        json.dumps(payload, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    os.replace(atomic, final)
                temp.unlink(missing_ok=True)
            except Exception:
                # A damaged orphan must never prevent integration startup.
                continue
