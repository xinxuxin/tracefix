from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

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
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_message: str = ""
    trace_path: str | None = None
    saved_patch_path: str | None = None

    def add_attempt(self, attempt: AttemptRecord) -> None:
        self.attempts.append(attempt)

    def mark_finished(
        self,
        *,
        status: str,
        final_message: str,
        saved_patch_path: str | None = None,
    ) -> None:
        self.status = status
        self.final_message = final_message
        if saved_patch_path is not None:
            self.saved_patch_path = saved_patch_path

