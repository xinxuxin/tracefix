from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from pathlib import Path


@dataclass
class ExecutionResult:
    """Captured result of bounded Python execution."""

    command: list[str]
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    exception_type: str | None = None
    exception_message: str | None = None
    failure_line: int | None = None
    outcome_label: str = "runtime_exception"
    traceback_text: str | None = None
    temp_file_path: str | None = None
    session_id: str | None = None
    used_interpreter: str | None = None
    blocked_reason: str | None = None
    policy_notes: list[str] = field(default_factory=list)
    expected_output: str | None = None

    @property
    def succeeded(self) -> bool:
        return not self.timed_out and self.return_code == 0

    @property
    def failure_signature(self) -> str:
        if self.timed_out:
            return "TimeoutError"
        if self.exception_type:
            return f"{self.exception_type}:{self.exception_message or ''}"
        return f"return_code:{self.return_code}"


@dataclass
class Diagnosis:
    """A narrow diagnosis produced by the diagnoser."""

    supported: bool
    bug_class: str
    summary: str
    evidence: list[str]
    confidence: float
    line_number: int | None = None
    target_name: str | None = None
    replacement_name: str | None = None
    stop_reason: str | None = None


@dataclass
class PatchCandidate:
    """A conservative patch candidate produced by the patcher."""

    strategy: str
    rationale: str
    patched_source: str
    changed_lines: list[int]


@dataclass
class VerificationResult:
    """Verifier output for a patched rerun."""

    success: bool
    summary: str
    failure_kind: str
    execution_result: ExecutionResult


@dataclass
class AttemptRecord:
    """One end-to-end attempt from diagnosis through verification."""

    attempt_index: int
    diagnosis: Diagnosis
    patch_candidate: PatchCandidate | None
    verification: VerificationResult | None


@dataclass
class SimpleTestSpec:
    """Optional execution hints supplied by the caller."""

    description: str = ""
    arguments: list[str] = field(default_factory=list)


@dataclass
class SessionMetadata:
    """Minimal metadata that ties an executor call to a controller session."""

    session_id: str
    target_file: str | None = None
    stage: str = "executor"
    attempt_index: int | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for one bounded executor run."""

    timeout_seconds: int = 2
    filename: str = "target.py"
    temp_dir_prefix: str = "tracefix_exec_"
    trace_log_path: Path = Path("logs/traces/execution_events.jsonl")
    interpreter_command: tuple[str, ...] = ("python3.11",)
    isolated_mode: bool = True
    bytecode_writes_disabled: bool = True


@dataclass
class ExecutionRequest:
    """Input contract for the executor agent/component."""

    code: str
    user_intent: str | None = None
    expected_output: str | None = None
    simple_test_spec: SimpleTestSpec | None = None
    session_metadata: SessionMetadata = field(
        default_factory=lambda: SessionMetadata(session_id="adhoc-execution")
    )
    execution_config: ExecutionConfig = field(default_factory=ExecutionConfig)


def to_dict(value: Any) -> Any:
    """Recursively convert dataclasses into JSON-serializable objects."""

    if hasattr(value, "__dataclass_fields__"):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value
