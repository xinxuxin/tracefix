"""Compatibility wrapper for the sandboxed executor."""

from __future__ import annotations

import sys
from pathlib import Path

from tracefix.sandbox.executor import Executor as SandboxedExecutor
from tracefix.sandbox.policy import SandboxPolicy


class Executor(SandboxedExecutor):
    """Backward-compatible executor used by the existing controller path."""

    def __init__(
        self,
        timeout_seconds: int = 2,
        policy: SandboxPolicy | None = None,
        trace_log_path: str | Path = "logs/traces/execution_events.jsonl",
        interpreter_command: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__(
            timeout_seconds=timeout_seconds,
            policy=policy,
            trace_log_path=trace_log_path,
            interpreter_command=interpreter_command or ("python3.11", sys.executable),
        )


__all__ = ["Executor"]
