from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

STATE_SAFE_IDLE = "SAFE_IDLE"
STATE_SHADOW_ACTIVE = "SHADOW_ACTIVE"
STATE_HOLD = "HOLD"
STATE_FAULT = "FAULT"
STATE_RECOVERY = "RECOVERY"
STATE_ARMED_LOCKED = "ARMED_LOCKED"


@dataclass(frozen=True)
class SafetyStateSnapshot:
    state: str
    reason: str
    since: str
    seconds_in_state: float
    shadow_authorized: bool
    transition_count: int
    hold_count: int
    fault_count: int
    recovery_count: int
    last_fault: str | None
    recovery_remaining_seconds: float
    fault_escalation_remaining_seconds: float


class SafetyStateMachine:
    """Runtime-only safety state machine for Sprint 6.

    It never enables real writes. It only decides whether a valid Shadow
    command is allowed to remain a `would_send_command` candidate.
    """

    def __init__(self, hold_to_fault_seconds: float = 30.0, recovery_seconds: float = 10.0):
        self.hold_to_fault_seconds = max(1.0, float(hold_to_fault_seconds))
        self.recovery_seconds = max(1.0, float(recovery_seconds))
        self.reset()

    def reset(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        self.state = STATE_SAFE_IDLE
        self.state_since = now
        self._fault_started_at = None
        self._recovery_started_at = None
        self.transition_count = 0
        self.hold_count = 0
        self.fault_count = 0
        self.recovery_count = 0
        self.last_fault = None
        self.reason = "Mode sécurisé par défaut"

    def _transition(self, state: str, reason: str, now: datetime) -> None:
        if state != self.state:
            self.state = state
            self.state_since = now
            self.transition_count += 1
            if state == STATE_HOLD:
                self.hold_count += 1
            elif state == STATE_FAULT:
                self.fault_count += 1
            elif state == STATE_RECOVERY:
                self.recovery_count += 1
        self.reason = reason

    def update(
        self,
        mode: str,
        safety_ok: bool,
        watchdog_state: str,
        safety_reason: str,
        now: datetime | None = None,
    ) -> SafetyStateSnapshot:
        now = now or datetime.now(timezone.utc)

        if mode == "Simulation":
            self._fault_started_at = None
            self._recovery_started_at = None
            self._transition(STATE_SAFE_IDLE, "Simulation — aucune commande réelle", now)
            return self.snapshot(now)

        if mode == "Armed":
            self._fault_started_at = None
            self._recovery_started_at = None
            self._transition(STATE_ARMED_LOCKED, "Armed verrouillé — écritures interdites", now)
            return self.snapshot(now)

        # Shadow mode
        if not safety_ok:
            self._recovery_started_at = None
            if self._fault_started_at is None:
                self._fault_started_at = now
                self.last_fault = f"{watchdog_state}: {safety_reason}"
                self._transition(STATE_HOLD, f"HOLD — {safety_reason}", now)
            else:
                elapsed = max(0.0, (now - self._fault_started_at).total_seconds())
                self.last_fault = f"{watchdog_state}: {safety_reason}"
                if elapsed >= self.hold_to_fault_seconds:
                    self._transition(STATE_FAULT, f"FAULT — {safety_reason}", now)
                elif self.state != STATE_HOLD:
                    self._transition(STATE_HOLD, f"HOLD — {safety_reason}", now)
                else:
                    self.reason = f"HOLD — {safety_reason}"
            return self.snapshot(now)

        # Raw sources are valid again.
        self._fault_started_at = None
        if self.state == STATE_SHADOW_ACTIVE:
            self.reason = "Shadow actif — sécurité validée"
            return self.snapshot(now)

        if self.state != STATE_RECOVERY:
            self._recovery_started_at = now
            self._transition(STATE_RECOVERY, "RECOVERY — stabilisation des sources", now)
            return self.snapshot(now)

        if self._recovery_started_at is None:
            self._recovery_started_at = now
        recovery_elapsed = max(0.0, (now - self._recovery_started_at).total_seconds())
        if recovery_elapsed >= self.recovery_seconds:
            self._recovery_started_at = None
            self._transition(STATE_SHADOW_ACTIVE, "Shadow actif — sécurité validée", now)
        else:
            remaining = max(0.0, self.recovery_seconds - recovery_elapsed)
            self.reason = f"RECOVERY — stabilisation ({remaining:.1f} s restantes)"
        return self.snapshot(now)

    def snapshot(self, now: datetime | None = None) -> SafetyStateSnapshot:
        now = now or datetime.now(timezone.utc)
        seconds = max(0.0, (now - self.state_since).total_seconds())
        recovery_remaining = 0.0
        if self.state == STATE_RECOVERY and self._recovery_started_at is not None:
            recovery_remaining = max(
                0.0,
                self.recovery_seconds - (now - self._recovery_started_at).total_seconds(),
            )
        fault_remaining = 0.0
        if self.state == STATE_HOLD and self._fault_started_at is not None:
            fault_remaining = max(
                0.0,
                self.hold_to_fault_seconds - (now - self._fault_started_at).total_seconds(),
            )
        return SafetyStateSnapshot(
            state=self.state,
            reason=self.reason,
            since=self.state_since.isoformat(),
            seconds_in_state=round(seconds, 1),
            shadow_authorized=self.state == STATE_SHADOW_ACTIVE,
            transition_count=self.transition_count,
            hold_count=self.hold_count,
            fault_count=self.fault_count,
            recovery_count=self.recovery_count,
            last_fault=self.last_fault,
            recovery_remaining_seconds=round(recovery_remaining, 1),
            fault_escalation_remaining_seconds=round(fault_remaining, 1),
        )
