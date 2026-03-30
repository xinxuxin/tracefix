from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tracefix.agents.diagnoser_agent import DiagnoserAgent
from tracefix.agents.executor_agent import ExecutorAgent
from tracefix.agents.patcher_agent import PatcherAgent
from tracefix.agents.verifier_agent import VerifierAgent
from tracefix.config import TraceFixConfig
from tracefix.logger import TraceLogger
from tracefix.state import SessionState
from tracefix.types import AttemptRecord
from tracefix.types import Diagnosis
from tracefix.types import DiagnoserRequest
from tracefix.types import DiagnoserResult
from tracefix.types import ExecutionConfig
from tracefix.types import ExecutionResult
from tracefix.types import PatchCandidate
from tracefix.types import PatcherRequest
from tracefix.types import PatcherResult
from tracefix.types import SessionMetadata
from tracefix.types import SimpleTestSpec
from tracefix.types import VerificationResult
from tracefix.types import VerifierRequest


class TraceFixController:
    """Coordinates the bounded end-to-end TraceFix workflow."""

    def __init__(
        self,
        config: TraceFixConfig | None = None,
        *,
        max_attempts: int = 2,
        timeout_seconds: int = 2,
        trace_dir: str | Path = "logs/traces",
        patch_dir: str | Path = "outputs/patches",
        session_root: str | Path | None = None,
    ) -> None:
        self.config = config or TraceFixConfig(
            max_attempts=max_attempts,
            timeout_seconds=timeout_seconds,
            trace_dir=Path(trace_dir),
            patch_dir=Path(patch_dir),
        )
        self.config.ensure_directories()
        self.executor = ExecutorAgent()
        self.diagnoser = DiagnoserAgent()
        self.patcher = PatcherAgent()
        self.verifier = VerifierAgent()
        self.logger = TraceLogger(
            trace_dir=self.config.trace_dir,
            patch_dir=self.config.patch_dir,
        )
        self.session_root = Path(session_root) if session_root is not None else (self.config.patch_dir.parent / "sessions")

    def debug_file(
        self,
        script_path: str | Path,
        *,
        expected_output: str | None = None,
        user_intent: str | None = None,
        simple_test_spec: SimpleTestSpec | None = None,
        max_retries: int | None = None,
    ) -> SessionState:
        path = Path(script_path)
        source = path.read_text(encoding="utf-8")
        retry_budget = max_retries if max_retries is not None else self.config.max_attempts
        session_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        session_dir = self.logger.create_session_dir(
            base_dir=self.session_root,
            file_stem=path.stem,
            session_id=session_id,
        )
        trace_events_path = session_dir / "trace.jsonl"
        patches_dir = session_dir / "patches"
        patches_dir.mkdir(parents=True, exist_ok=True)

        original_execution = self._run_executor(
            code=source,
            filename=path.name,
            session_id=session_id,
            trace_events_path=trace_events_path,
            target_file=str(path),
            expected_output=expected_output,
            simple_test_spec=simple_test_spec,
            attempt_index=0,
        )

        state = SessionState(
            session_id=session_id,
            target_file=str(path),
            max_attempts=retry_budget,
            timeout_seconds=self.config.timeout_seconds,
            status="running",
            started_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            original_execution=original_execution,
            expected_output=expected_output,
            session_dir=str(session_dir),
            trace_events_path=str(trace_events_path),
            summary_path=str(session_dir / "summary.md"),
        )

        self._persist_state(state)

        if original_execution.succeeded and self._initial_behavior_acceptable(original_execution, expected_output):
            state.mark_finished(
                status="no_failure_detected",
                final_message="The provided script already executed successfully and matched the available behavior check.",
                final_decision="accept",
                behavior_match_status=self._initial_behavior_status(original_execution, expected_output),
            )
            self._finalize_session(state)
            return state

        current_code = source
        current_execution = original_execution
        prior_patch_history: list[str] = []
        prior_verifier_feedback: list[str] = []

        for attempt_index in range(1, retry_budget + 1):
            diagnosis = self._run_diagnoser(
                code=current_code,
                execution_result=current_execution,
                user_intent=user_intent,
                expected_output=expected_output,
                prior_patch_history=prior_patch_history,
                prior_verifier_feedback=prior_verifier_feedback,
                trace_events_path=trace_events_path,
                attempt_index=attempt_index,
            )

            patch_result = self._run_patcher(
                code=current_code,
                diagnosis=diagnosis,
                user_intent=user_intent,
                prior_patch_history=prior_patch_history,
                prior_verifier_feedback=prior_verifier_feedback,
                trace_events_path=trace_events_path,
                attempt_index=attempt_index,
            )

            rerun_execution: ExecutionResult | None = None
            verifier_result = None
            patch_path: Path | None = None
            diff_path: Path | None = None

            if patch_result.refusal_reason is None:
                patch_path = patches_dir / f"attempt_{attempt_index:02d}_candidate.py"
                diff_path = patches_dir / f"attempt_{attempt_index:02d}.diff"
                self.logger.write_text(patch_path, patch_result.updated_code)
                self.logger.write_text(diff_path, patch_result.patch_diff)
                state.intermediate_patch_paths.append(str(patch_path))

                self._handoff_event(
                    trace_events_path,
                    handoff="patcher -> executor",
                    attempt_index=attempt_index,
                    summary=patch_result.patch_summary,
                    payload={
                        "strategy_id": patch_result.strategy_id,
                        "minimality_flag": patch_result.minimality_flag,
                    },
                )
                rerun_execution = self._run_executor(
                    code=patch_result.updated_code,
                    filename=path.name,
                    session_id=session_id,
                    trace_events_path=trace_events_path,
                    target_file=str(path),
                    expected_output=expected_output,
                    simple_test_spec=simple_test_spec,
                    attempt_index=attempt_index,
                )

                verifier_result = self._run_verifier(
                    original_code=current_code,
                    patched_code=patch_result.updated_code,
                    original_execution=current_execution,
                    rerun_execution=rerun_execution,
                    expected_output=expected_output,
                    simple_test_spec=simple_test_spec,
                    diagnosis=diagnosis,
                    patch_result=patch_result,
                    retry_count=attempt_index - 1,
                    max_retries=retry_budget,
                    trace_events_path=trace_events_path,
                    attempt_index=attempt_index,
                )

            state.add_attempt(
                AttemptRecord(
                    attempt_index=attempt_index,
                    diagnosis=self._to_legacy_diagnosis(diagnosis),
                    patch_candidate=self._to_legacy_patch(patch_result),
                    verification=self._to_legacy_verification(verifier_result, rerun_execution),
                )
            )
            state.add_attempt_detail(
                {
                    "attempt_index": attempt_index,
                    "diagnosis_result": diagnosis,
                    "patch_result": patch_result,
                    "rerun_execution_result": rerun_execution,
                    "verifier_result": verifier_result,
                    "patch_path": str(patch_path) if patch_path is not None else None,
                    "diff_path": str(diff_path) if diff_path is not None else None,
                }
            )
            self._persist_state(state)

            if patch_result.refusal_reason is not None:
                state.mark_finished(
                    status="stopped_no_patch",
                    final_message=patch_result.refusal_reason,
                    final_decision="stop",
                    failure_summary_path=str(self._write_failure_summary(state, diagnosis, patch_result, None)),
                )
                self._finalize_session(state)
                return state

            assert rerun_execution is not None
            assert verifier_result is not None

            prior_patch_history.append(
                f"attempt {attempt_index}: strategy={patch_result.strategy_id}; summary={patch_result.patch_summary}"
            )
            prior_verifier_feedback.extend(verifier_result.targeted_feedback_for_retry)

            if verifier_result.decision == "accept":
                final_patch_path = session_dir / "final_patched_script.py"
                self.logger.write_text(final_patch_path, patch_result.updated_code)
                state.mark_finished(
                    status="fixed",
                    final_message=verifier_result.rationale,
                    saved_patch_path=str(final_patch_path),
                    final_decision=verifier_result.decision,
                    behavior_match_status=verifier_result.behavior_match_status,
                )
                self._finalize_session(state)
                return state

            if verifier_result.decision == "retry":
                current_code = patch_result.updated_code
                current_execution = rerun_execution
                continue

            status = "escalated_for_human_review" if verifier_result.decision == "escalate" else "max_attempts_reached"
            state.mark_finished(
                status=status,
                final_message=verifier_result.rationale,
                final_decision=verifier_result.decision,
                behavior_match_status=verifier_result.behavior_match_status,
                failure_summary_path=str(self._write_failure_summary(state, diagnosis, patch_result, verifier_result)),
            )
            self._finalize_session(state)
            return state

        last_attempt = state.attempt_details[-1] if state.attempt_details else {}
        last_diagnosis = last_attempt.get("diagnosis_result") if isinstance(last_attempt, dict) else None
        last_patch = last_attempt.get("patch_result") if isinstance(last_attempt, dict) else None
        last_verifier = last_attempt.get("verifier_result") if isinstance(last_attempt, dict) else None
        state.mark_finished(
            status="max_attempts_reached",
            final_message="Retry budget exhausted before the patch could be accepted.",
            final_decision="stop",
            behavior_match_status=getattr(last_verifier, "behavior_match_status", None),
            failure_summary_path=str(self._write_failure_summary(state, last_diagnosis, last_patch, last_verifier)),
        )
        self._finalize_session(state)
        return state

    def _run_executor(
        self,
        *,
        code: str,
        filename: str,
        session_id: str,
        trace_events_path: Path,
        target_file: str,
        expected_output: str | None,
        simple_test_spec: SimpleTestSpec | None,
        attempt_index: int,
    ) -> ExecutionResult:
        self._handoff_event(
            trace_events_path,
            handoff="controller -> executor",
            attempt_index=attempt_index,
            summary="Controller requested bounded Python execution.",
        )
        result = self.executor.run(
            code=code,
            expected_output=expected_output,
            simple_test_spec=simple_test_spec,
            session_metadata=SessionMetadata(
                session_id=session_id,
                target_file=target_file,
                stage="executor",
                attempt_index=attempt_index,
            ),
            execution_config=ExecutionConfig(
                timeout_seconds=self.config.timeout_seconds,
                filename=filename,
                trace_log_path=trace_events_path,
                interpreter_command=("python3.11", "python3"),
            ),
        )
        return result

    def _run_diagnoser(
        self,
        *,
        code: str,
        execution_result: ExecutionResult,
        user_intent: str | None,
        expected_output: str | None,
        prior_patch_history: list[str],
        prior_verifier_feedback: list[str],
        trace_events_path: Path,
        attempt_index: int,
    ) -> DiagnoserResult:
        self._handoff_event(
            trace_events_path,
            handoff="executor -> diagnoser",
            attempt_index=attempt_index,
            summary=f"Executor returned {execution_result.outcome_label}.",
            payload={
                "exception_type": execution_result.exception_type,
                "failure_line": execution_result.failure_line,
            },
        )
        return self.diagnoser.diagnose(
            DiagnoserRequest(
                code=code,
                latest_execution_result=execution_result,
                user_intent=user_intent,
                expected_output=expected_output,
                prior_patch_history=prior_patch_history,
                prior_verifier_feedback=prior_verifier_feedback,
                session_state_summary=f"attempt={attempt_index}; prior_patches={len(prior_patch_history)}",
            )
        )

    def _run_patcher(
        self,
        *,
        code: str,
        diagnosis: DiagnoserResult,
        user_intent: str | None,
        prior_patch_history: list[str],
        prior_verifier_feedback: list[str],
        trace_events_path: Path,
        attempt_index: int,
    ) -> PatcherResult:
        self._handoff_event(
            trace_events_path,
            handoff="diagnoser -> patcher",
            attempt_index=attempt_index,
            summary=diagnosis.likely_root_cause,
            payload={
                "primary_bug_class": diagnosis.primary_bug_class,
                "confidence_score": diagnosis.confidence_score,
            },
        )
        return self.patcher.patch(
            PatcherRequest(
                code=code,
                diagnosis_result=diagnosis,
                user_intent=user_intent,
                prior_patch_history=prior_patch_history,
                verifier_feedback=prior_verifier_feedback,
            )
        )

    def _run_verifier(
        self,
        *,
        original_code: str,
        patched_code: str,
        original_execution: ExecutionResult,
        rerun_execution: ExecutionResult,
        expected_output: str | None,
        simple_test_spec: SimpleTestSpec | None,
        diagnosis: DiagnoserResult,
        patch_result: PatcherResult,
        retry_count: int,
        max_retries: int,
        trace_events_path: Path,
        attempt_index: int,
    ):
        self._handoff_event(
            trace_events_path,
            handoff="executor -> verifier",
            attempt_index=attempt_index,
            summary=f"Patched rerun ended with {rerun_execution.outcome_label}.",
            payload={
                "return_code": rerun_execution.return_code,
                "stdout": rerun_execution.stdout,
            },
        )
        result = self.verifier.verify(
            VerifierRequest(
                original_code=original_code,
                patched_code=patched_code,
                original_execution_result=original_execution,
                rerun_execution_result=rerun_execution,
                expected_output=expected_output,
                simple_test_spec=simple_test_spec,
                diagnosis_result=diagnosis,
                patch_result=patch_result,
                retry_count=retry_count,
                max_retries=max_retries,
            )
        )
        self._handoff_event(
            trace_events_path,
            handoff="verifier -> controller",
            attempt_index=attempt_index,
            summary=result.rationale,
            payload={
                "decision": result.decision,
                "behavior_match_status": result.behavior_match_status,
                "regression_flags": result.regression_flags,
            },
        )
        return result

    def _handoff_event(
        self,
        trace_events_path: Path,
        *,
        handoff: str,
        attempt_index: int,
        summary: str,
        payload: dict[str, object] | None = None,
    ) -> None:
        self.logger.append_event(
            trace_events_path,
            {
                "event": "handoff",
                "handoff": handoff,
                "attempt_index": attempt_index,
                "summary": summary,
                "payload": payload or {},
            },
        )

    def _persist_state(self, state: SessionState) -> None:
        state.handoff_count = self._count_handoffs(state.trace_events_path)
        assert state.session_dir is not None
        self.logger.write_state_snapshot(state, Path(state.session_dir) / "session_state.json")

    def _finalize_session(self, state: SessionState) -> None:
        self._persist_state(state)
        assert state.summary_path is not None
        self.logger.write_text(state.summary_path, self._build_markdown_summary(state))

    def _write_failure_summary(
        self,
        state: SessionState,
        diagnosis: DiagnoserResult | None,
        patch_result: PatcherResult | None,
        verifier_result,
    ) -> Path:
        assert state.session_dir is not None
        destination = Path(state.session_dir) / "failure_summary.md"
        lines = [
            "# Failure Summary",
            "",
            f"- Session ID: `{state.session_id}`",
            f"- Final status: `{state.status}`",
            f"- Final decision: `{state.final_decision or 'stop'}`",
            "",
        ]
        if diagnosis is not None:
            lines.extend(
                [
                    "## Latest Diagnosis",
                    "",
                    f"- Bug class: `{diagnosis.primary_bug_class}`",
                    f"- Root cause hypothesis: {diagnosis.likely_root_cause}",
                    f"- Uncertainty: {diagnosis.uncertainty_notes}",
                    "",
                ]
            )
        if patch_result is not None:
            lines.extend(
                [
                    "## Latest Patch Attempt",
                    "",
                    f"- Patch summary: {patch_result.patch_summary}",
                    f"- Strategy: `{patch_result.strategy_id or 'none'}`",
                    f"- Refusal reason: {patch_result.refusal_reason or 'none'}",
                    "",
                ]
            )
        if verifier_result is not None:
            lines.extend(
                [
                    "## Verifier Outcome",
                    "",
                    f"- Decision: `{verifier_result.decision}`",
                    f"- Rationale: {verifier_result.rationale}",
                    f"- Retry feedback: {'; '.join(verifier_result.targeted_feedback_for_retry) or 'none'}",
                    "",
                ]
            )
        return self.logger.write_text(destination, "\n".join(lines))

    def _build_markdown_summary(self, state: SessionState) -> str:
        lines = [
            "# TraceFix Session Summary",
            "",
            f"- Session ID: `{state.session_id}`",
            f"- Target file: `{state.target_file}`",
            f"- Status: `{state.status}`",
            f"- Final decision: `{state.final_decision or 'n/a'}`",
            f"- Final message: {state.final_message}",
            f"- Attempts used: {len(state.attempts)} / {state.max_attempts}",
            f"- Behavior match: `{state.behavior_match_status or 'n/a'}`",
            f"- Session directory: `{state.session_dir}`",
            f"- Trace JSONL: `{state.trace_events_path}`",
            f"- State snapshot: `{state.trace_path}`",
        ]
        if state.saved_patch_path:
            lines.append(f"- Accepted patch: `{state.saved_patch_path}`")
        if state.failure_summary_path:
            lines.append(f"- Failure summary: `{state.failure_summary_path}`")
        if state.intermediate_patch_paths:
            lines.append("")
            lines.append("## Intermediate Patches")
            lines.append("")
            for patch_path in state.intermediate_patch_paths:
                lines.append(f"- `{patch_path}`")
        if state.attempt_details:
            lines.append("")
            lines.append("## Attempt Outcomes")
            lines.append("")
            for detail in state.attempt_details:
                diagnosis = detail.get("diagnosis_result")
                patch_result = detail.get("patch_result")
                verifier_result = detail.get("verifier_result")
                lines.append(
                    f"- Attempt {detail['attempt_index']}: "
                    f"diagnosis=`{getattr(diagnosis, 'primary_bug_class', 'n/a')}`, "
                    f"patch=`{getattr(patch_result, 'strategy_id', None) or 'refused'}`, "
                    f"verifier=`{getattr(verifier_result, 'decision', 'not_run')}`"
                )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _initial_behavior_acceptable(result: ExecutionResult, expected_output: str | None) -> bool:
        if not result.succeeded:
            return False
        if expected_output is None:
            return True
        return result.stdout.strip() == expected_output.strip()

    @staticmethod
    def _initial_behavior_status(result: ExecutionResult, expected_output: str | None) -> str:
        if expected_output is None:
            return "no_behavior_oracle"
        return "matched_expected_output" if result.stdout.strip() == expected_output.strip() else "mismatched_expected_output"

    @staticmethod
    def _count_handoffs(trace_events_path: str | None) -> int:
        if trace_events_path is None:
            return 0
        path = Path(trace_events_path)
        if not path.exists():
            return 0
        count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if '"event": "handoff"' in line:
                count += 1
        return count

    @staticmethod
    def _to_legacy_diagnosis(diagnosis: DiagnoserResult) -> Diagnosis:
        bug_class = diagnosis.primary_bug_class
        target_name = diagnosis.repair_hints.get("target_name")
        replacement_name = diagnosis.repair_hints.get("replacement_name")
        supported = any(
            diagnosis.repair_hints.get(key)
            for key in ("missing_colon", "replacement_name", "remove_call_arguments", "missing_path")
        )
        if bug_class == "syntax_error" and diagnosis.repair_hints.get("missing_colon"):
            bug_class = "missing_colon"
        elif bug_class == "name_error" and replacement_name:
            bug_class = "name_error_typo"
        return Diagnosis(
            supported=supported,
            bug_class=bug_class,
            summary=diagnosis.likely_root_cause,
            evidence=diagnosis.evidence_summary,
            confidence=diagnosis.confidence_score,
            line_number=diagnosis.localized_code_region.start_line,
            target_name=target_name if isinstance(target_name, str) else None,
            replacement_name=replacement_name if isinstance(replacement_name, str) else None,
            stop_reason=None if supported else "unsupported_failure",
        )

    @staticmethod
    def _to_legacy_patch(patch_result: PatcherResult) -> PatchCandidate | None:
        if patch_result.refusal_reason is not None:
            return None
        return PatchCandidate(
            strategy=patch_result.strategy_id or "bounded_patch",
            rationale=patch_result.patch_summary,
            patched_source=patch_result.updated_code,
            changed_lines=[region.start_line for region in patch_result.changed_regions],
        )

    @staticmethod
    def _to_legacy_verification(
        verifier_result,
        rerun_execution: ExecutionResult | None,
    ) -> VerificationResult | None:
        if verifier_result is None or rerun_execution is None:
            return None
        return VerificationResult(
            success=verifier_result.decision == "accept",
            summary=verifier_result.rationale,
            failure_kind=verifier_result.decision,
            execution_result=rerun_execution,
        )
