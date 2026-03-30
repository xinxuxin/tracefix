from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


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


@dataclass
class CodeRegion:
    """Localized code region referenced by the diagnoser."""

    start_line: int | None = None
    end_line: int | None = None
    snippet: str = ""


@dataclass
class AlternativeHypothesis:
    """Optional alternative explanation when evidence is not fully decisive."""

    bug_class: str
    reason: str
    confidence_band: str


@dataclass
class DiagnoserRequest:
    """Input contract for the diagnoser component."""

    code: str
    latest_execution_result: ExecutionResult
    user_intent: str | None = None
    expected_output: str | None = None
    prior_patch_history: list[str] = field(default_factory=list)
    prior_verifier_feedback: list[str] = field(default_factory=list)
    session_state_summary: str = ""


@dataclass
class DiagnoserResult:
    """Structured diagnosis handed off to the patcher/controller."""

    primary_bug_class: str
    likely_root_cause: str
    localized_code_region: CodeRegion
    evidence_summary: list[str]
    recommended_repair_direction: str
    confidence_score: float
    confidence_band: str
    uncertainty_notes: str
    alternative_hypotheses: list[AlternativeHypothesis] = field(default_factory=list)
    direct_cause: str | None = None
    downstream_symptom: str | None = None
    repair_hints: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatchChangedRegion:
    """A localized before/after region touched by the patcher."""

    start_line: int
    end_line: int
    original_snippet: str
    updated_snippet: str


@dataclass
class PatcherRequest:
    """Input contract for the patcher component."""

    code: str
    diagnosis_result: DiagnoserResult
    user_intent: str | None = None
    prior_patch_history: list[str] = field(default_factory=list)
    verifier_feedback: list[str] = field(default_factory=list)


@dataclass
class PatcherResult:
    """Structured patch synthesis result."""

    updated_code: str
    patch_diff: str
    changed_regions: list[PatchChangedRegion]
    patch_summary: str
    intended_effect: str
    minimality_flag: str
    confidence_score: float
    refusal_reason: str | None = None
    strategy_id: str | None = None


@dataclass
class VerifierRequest:
    """Input contract for the verifier component."""

    original_code: str
    patched_code: str
    original_execution_result: ExecutionResult
    rerun_execution_result: ExecutionResult
    expected_output: str | None = None
    simple_test_spec: SimpleTestSpec | None = None
    diagnosis_result: DiagnoserResult | None = None
    patch_result: PatcherResult | None = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class VerifierResult:
    """Structured decision from the verifier."""

    decision: str
    rationale: str
    regression_flags: list[str]
    behavior_match_status: str
    original_failure_resolved: bool
    uncertainty_notes: str
    targeted_feedback_for_retry: list[str] = field(default_factory=list)


def to_dict(value: Any) -> Any:
    """Recursively convert dataclasses into JSON-serializable objects."""

    if hasattr(value, "__dataclass_fields__"):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    return value
