from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

GATE_LOCKED = "LOCKED"
GATE_READY_LOCKED = "READY_LOCKED"

REASON_GLOBAL_LOCK = "GLOBAL_WRITE_LOCK"
REASON_REAL_WRITES_DISABLED = "REAL_WRITES_DISABLED"
REASON_PIPELINE_LOCK = "PIPELINE_WRITE_LOCKED"
REASON_ADAPTER_LOCK = "ADAPTER_WRITE_LOCKED"
REASON_SAFETY = "SAFETY_NOT_AUTHORIZED"
REASON_PLAN = "PLAN_NOT_EXECUTABLE"
REASON_READY = "ALL_GATES_SATISFIED_BUT_MASTER_LOCKED"


@dataclass(frozen=True)
class WriteGateInput:
    safety_ok: bool
    pipeline_write_locked: bool
    adapter_write_locked: bool
    real_writes_enabled: bool
    hyper_plan_supported: bool
    solarflow_plan_supported: bool
    hyper_would_execute: bool
    solarflow_would_execute: bool


@dataclass(frozen=True)
class WriteGateDecision:
    state: str
    execute_allowed: bool
    master_lock: bool
    blockers: tuple[str, ...]
    evaluated_at: str


def evaluate_write_gate(context: WriteGateInput) -> WriteGateDecision:
    """Evaluate the final hardware barrier without executing any command.

    alpha.3.12 deliberately keeps a non-bypassable master lock. Even if every
    upstream condition becomes valid, execute_allowed remains False.
    """
    blockers: list[str] = []
    if not context.real_writes_enabled:
        blockers.append(REASON_REAL_WRITES_DISABLED)
    if context.pipeline_write_locked:
        blockers.append(REASON_PIPELINE_LOCK)
    if context.adapter_write_locked:
        blockers.append(REASON_ADAPTER_LOCK)
    if not context.safety_ok:
        blockers.append(REASON_SAFETY)
    if not (context.hyper_plan_supported and context.solarflow_plan_supported):
        blockers.append(REASON_PLAN)

    # Permanent alpha.3.12 barrier. There is intentionally no execution branch.
    master_lock = True
    blockers.append(REASON_GLOBAL_LOCK)

    upstream_ready = (
        context.real_writes_enabled
        and not context.pipeline_write_locked
        and not context.adapter_write_locked
        and context.safety_ok
        and context.hyper_plan_supported
        and context.solarflow_plan_supported
        and (context.hyper_would_execute or context.solarflow_would_execute)
    )
    state = GATE_READY_LOCKED if upstream_ready else GATE_LOCKED

    return WriteGateDecision(
        state=state,
        execute_allowed=False,
        master_lock=master_lock,
        blockers=tuple(blockers),
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
