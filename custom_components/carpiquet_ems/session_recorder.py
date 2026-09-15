from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any, Iterator


class _RecoverySummary:
    """Incremental summary builder: memory use does not grow with session size."""

    def __init__(self) -> None:
        self.count = 0
        self.perf_sum = 0.0
        self.zendure_sum = 0.0
        self.perf_count = 0
        self.real_import = self.real_export = 0.0
        self.sim_import = self.sim_export = 0.0
        self.pv_charged = self.pv_curtailed = 0.0
        self.recorded_seconds = 0.0
        self.missing_intervals = 0
        self.longest_interval = 0.0
        self.last: dict[str, Any] | None = None

    @staticmethod
    def _number(sample: dict[str, Any], key: str) -> float:
        try:
            return float(sample.get(key, 0.0) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def add(self, sample: dict[str, Any]) -> None:
        self.count += 1
        self.last = sample

        try:
            dt = max(0.0, float(sample.get("cycle_seconds", 0.0)))
        except (TypeError, ValueError):
            dt = 0.0
        self.recorded_seconds += dt
        self.longest_interval = max(self.longest_interval, dt)
        if dt > 10.0:
            self.missing_intervals += 1
        dt_h = dt / 3600.0

        perf = sample.get("performance_score_percent")
        zendure = sample.get("zendure_reference_score_percent")
        try:
            perf_value = float(perf)
            zendure_value = float(zendure)
        except (TypeError, ValueError):
            pass
        else:
            self.perf_sum += perf_value
            self.zendure_sum += zendure_value
            self.perf_count += 1

        real_grid = self._number(sample, "grid_real_w")
        sim_grid = self._number(sample, "grid_simulated_w")
        self.real_import += max(0.0, real_grid) * dt_h / 1000.0
        self.real_export += max(0.0, -real_grid) * dt_h / 1000.0
        self.sim_import += max(0.0, sim_grid) * dt_h / 1000.0
        self.sim_export += max(0.0, -sim_grid) * dt_h / 1000.0
        self.pv_charged += max(
            0.0,
            self._number(sample, "hyper_simulated_charge_w")
            + self._number(sample, "solarflow_simulated_charge_w"),
        ) * dt_h / 1000.0
        self.pv_curtailed += max(
            0.0, self._number(sample, "pv_curtailed_w")
        ) * dt_h / 1000.0

    def build(self) -> dict[str, Any]:
        if not self.last:
            return {
                "status": "session interrompue",
                "performance_samples": 0,
                "recorded_duration_seconds": 0.0,
                "missing_data_intervals": 0,
                "longest_interval_seconds": 0.0,
            }

        return {
            "status": "session interrompue — résumé recalculé",
            "performance_score_percent": self.last.get("performance_score_percent"),
            "zendure_reference_score_percent": self.last.get(
                "zendure_reference_score_percent"
            ),
            "virtual_hyper_energy_kwh": None,
            "virtual_solarflow_energy_kwh": None,
            "performance_samples": self.perf_count,
            "performance_average_percent": (
                round(self.perf_sum / self.perf_count, 2)
                if self.perf_count
                else None
            ),
            "zendure_average_percent": (
                round(self.zendure_sum / self.perf_count, 2)
                if self.perf_count
                else None
            ),
            "real_import_energy_kwh": round(self.real_import, 4),
            "real_export_energy_kwh": round(self.real_export, 4),
            "sim_import_energy_kwh": round(self.sim_import, 4),
            "sim_export_energy_kwh": round(self.sim_export, 4),
            "pv_charged_energy_kwh": round(self.pv_charged, 4),
            "pv_curtailed_energy_kwh": round(self.pv_curtailed, 4),
            "recorded_duration_seconds": round(self.recorded_seconds, 1),
            "missing_data_intervals": self.missing_intervals,
            "longest_interval_seconds": round(self.longest_interval, 3),
            "last_sample_timestamp": self.last.get("timestamp"),
        }


class SimulationSessionRecorder:
    """Thread-safe, bounded-memory simulation recorder with atomic finalization."""

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
        # Report filenames are cached. Home Assistant entity properties must not
        # perform filesystem I/O on the event loop.
        self._reports: list[str] = []

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

    def _refresh_reports(self) -> None:
        """Refresh report cache. Call only from recorder executor jobs."""
        reports = sorted(
            (p.name for p in self._base_dir().glob("SIM-*.json")),
            reverse=True,
        )
        with self._lock:
            self._reports = reports

    def list_reports(self) -> list[str]:
        """Return cached report names without touching the filesystem."""
        with self._lock:
            return list(self._reports)

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

    @staticmethod
    def _read_header(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as src:
            first = src.readline()
        if not first.strip():
            return {}
        header = json.loads(first)
        if not isinstance(header, dict):
            raise ValueError("Invalid JSONL header")
        return header

    @staticmethod
    def _iter_sample_lines(path: Path) -> Iterator[str]:
        """Yield one validated sample line at a time; never retains the session."""
        with path.open("r", encoding="utf-8") as src:
            src.readline()  # header
            for line in src:
                if line.strip():
                    yield line.rstrip("\r\n")

    @staticmethod
    def _write_prefix(
        fh,
        session: dict[str, Any],
        initial_state: dict[str, Any],
        configuration: dict[str, Any],
    ) -> None:
        fh.write('{"session":')
        json.dump(session, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(',"initial_state":')
        json.dump(initial_state, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(',"configuration":')
        json.dump(configuration, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(',"samples":[')

    @staticmethod
    def _finish_atomic(fh, atomic: Path, final: Path) -> None:
        fh.flush()
        os.fsync(fh.fileno())
        fh.close()
        os.replace(atomic, final)

    def _stream_finalize(
        self,
        samples_path: Path,
        final: Path,
        session: dict[str, Any],
        initial_state: dict[str, Any],
        configuration: dict[str, Any],
        summary: dict[str, Any] | None,
        rebuild_summary: bool,
    ) -> tuple[int, dict[str, Any]]:
        atomic = final.with_name(f".{final.name}.tmp")
        recovery = _RecoverySummary() if rebuild_summary else None
        count = 0
        fh = None
        try:
            fh = atomic.open("w", encoding="utf-8")
            self._write_prefix(
                fh, session, initial_state, configuration
            )
            first = True
            for raw in self._iter_sample_lines(samples_path):
                # Recovery must validate and summarize each record, but only one
                # sample object exists in memory at any time.
                if recovery is not None:
                    sample = json.loads(raw)
                    if not isinstance(sample, dict):
                        raise ValueError("Invalid JSONL sample")
                    recovery.add(sample)
                if not first:
                    fh.write(",")
                fh.write(raw)
                first = False
                count += 1

            final_summary = recovery.build() if recovery is not None else (summary or {})
            fh.write('],"summary":')
            json.dump(
                final_summary,
                fh,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            fh.write("}")
            self._finish_atomic(fh, atomic, final)
            fh = None
            return count, final_summary
        except Exception:
            if fh is not None and not fh.closed:
                fh.close()
            atomic.unlink(missing_ok=True)
            raise

    def stop(
        self,
        summary: dict[str, Any],
        termination: str = "user_stop",
    ) -> str | None:
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
                header = self._read_header(samples_path)
                ended = datetime.now(timezone.utc)
                session = {
                    **header.get("session", {}),
                    "ended_at": ended.isoformat(),
                    "duration_seconds": round(
                        (ended - started_at).total_seconds(), 1
                    ),
                    # sample_count is the accepted count maintained during capture.
                    "cycles": self.sample_count,
                    "termination": termination,
                }
                final = self._base_dir() / f"{sid}.json"
                count, _ = self._stream_finalize(
                    samples_path=samples_path,
                    final=final,
                    session=session,
                    initial_state=header.get("initial_state", {}),
                    configuration=header.get("configuration", {}),
                    summary=summary,
                    rebuild_summary=False,
                )
                # Defensive correction if the file count differs from the counter.
                if count != session["cycles"]:
                    # Rewriting only the small metadata would complicate atomicity;
                    # preserve the valid report and surface the mismatch for diagnosis.
                    self.last_error = (
                        f"Cycle count mismatch: counter={session['cycles']} file={count}"
                    )
                else:
                    self.last_error = None

                samples_path.unlink(missing_ok=True)
                self.last_file = str(final)
                self.last_ended_at = ended.isoformat()
                self._refresh_reports()
                return self.last_file
            except Exception as err:
                # Keep the JSONL intact for a later recovery attempt.
                self.last_error = f"{type(err).__name__}: {err}"
                raise
            finally:
                self.session_id = None
                self.started_at = None
                self._samples_path = None
                self.sample_count = 0
                self.finalizing = False

    def finalize_orphaned_sessions(self) -> None:
        """Recover interrupted JSONL sessions with bounded memory."""
        for temp in self._base_dir().glob(".SIM-*.jsonl"):
            try:
                header = self._read_header(temp)
                if not header:
                    temp.unlink(missing_ok=True)
                    continue

                sid = (
                    header.get("session", {}).get("id")
                    or temp.name.removeprefix(".").removesuffix(".jsonl")
                )
                final = self._base_dir() / f"{sid}.json"
                if final.exists():
                    temp.unlink(missing_ok=True)
                    continue

                ended = datetime.fromtimestamp(temp.stat().st_mtime, tz=timezone.utc)
                started_raw = header.get("session", {}).get("started_at")
                duration = None
                if started_raw:
                    try:
                        started = datetime.fromisoformat(started_raw)
                        duration = round((ended - started).total_seconds(), 1)
                    except (TypeError, ValueError):
                        pass

                # First pass counts lines without retaining them. This lets the
                # final JSON contain the correct cycles metadata before samples.
                cycles = sum(1 for _ in self._iter_sample_lines(temp))
                session = {
                    **header.get("session", {}),
                    "ended_at": ended.isoformat(),
                    "duration_seconds": duration,
                    "cycles": cycles,
                    "termination": "home_assistant_interruption",
                }

                self._stream_finalize(
                    samples_path=temp,
                    final=final,
                    session=session,
                    initial_state=header.get("initial_state", {}),
                    configuration=header.get("configuration", {}),
                    summary=None,
                    rebuild_summary=True,
                )
                temp.unlink(missing_ok=True)
            except Exception as err:
                # A damaged or oversized orphan must never prevent HA startup.
                self.last_error = f"{type(err).__name__}: {err}"
                continue
        self._refresh_reports()
