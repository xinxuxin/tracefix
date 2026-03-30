from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from tracefix.types import AttemptRecord
from tracefix.types import ExecutionResult


@dataclass
class SessionState:
    """Lightweight controller state recorded for every debug session."""

    session_id: str
    target_file: str
    max_attempts: int
    timeout_seconds: int
    status: str
    started_at: str
    original_execution: ExecutionResult
    expected_output: str | None = None
    session_dir: str | None = None
    attempts: list[AttemptRecord] = field(default_factory=list)
    attempt_details: list[dict[str, Any]] = field(default_factory=list)
    trace_events_path: str | None = None
    final_message: str = ""
    trace_path: str | None = None
    saved_patch_path: str | None = None
    summary_path: str | None = None
    failure_summary_path: str | None = None
    intermediate_patch_paths: list[str] = field(default_factory=list)
    final_decision: str | None = None
    behavior_match_status: str | None = None
    handoff_count: int = 0

    def add_attempt(self, attempt: AttemptRecord) -> None:
        self.attempts.append(attempt)

    def add_attempt_detail(self, detail: dict[str, Any]) -> None:
        self.attempt_details.append(detail)

    def mark_finished(
        self,
        *,
        status: str,
        final_message: str,
        saved_patch_path: str | None = None,
        final_decision: str | None = None,
        behavior_match_status: str | None = None,
        failure_summary_path: str | None = None,
    ) -> None:
        self.status = status
        self.final_message = final_message
        if saved_patch_path is not None:
            self.saved_patch_path = saved_patch_path
        if final_decision is not None:
            self.final_decision = final_decision
        if behavior_match_status is not None:
            self.behavior_match_status = behavior_match_status
        if failure_summary_path is not None:
            self.failure_summary_path = failure_summary_path
