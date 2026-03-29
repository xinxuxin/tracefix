from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tracefix.config import TraceFixConfig
from tracefix.diagnoser import Diagnoser
from tracefix.executor import Executor
from tracefix.logger import TraceLogger
from tracefix.patcher import Patcher
from tracefix.state import SessionState
from tracefix.types import AttemptRecord
from tracefix.verifier import Verifier


class TraceFixController:
    """Coordinates execution, diagnosis, patching, verification, and logging."""

    def __init__(
        self,
        config: TraceFixConfig | None = None,
        *,
        max_attempts: int = 2,
        timeout_seconds: int = 2,
        trace_dir: str | Path = "logs/traces",
        patch_dir: str | Path = "outputs/patches",
    ) -> None:
        self.config = config or TraceFixConfig(
            max_attempts=max_attempts,
            timeout_seconds=timeout_seconds,
            trace_dir=Path(trace_dir),
            patch_dir=Path(patch_dir),
        )
        self.config.ensure_directories()
        self.executor = Executor(timeout_seconds=self.config.timeout_seconds)
        self.diagnoser = Diagnoser()
        self.patcher = Patcher()
        self.verifier = Verifier(self.executor)
        self.logger = TraceLogger(
            trace_dir=self.config.trace_dir,
            patch_dir=self.config.patch_dir,
        )

    def debug_file(self, script_path: str | Path) -> SessionState:
        path = Path(script_path)
        source = path.read_text(encoding="utf-8")
        session_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")

        original_result = self.executor.run_source(source, filename=path.name)
        state = SessionState(
            session_id=session_id,
            target_file=str(path),
            max_attempts=self.config.max_attempts,
            timeout_seconds=self.config.timeout_seconds,
            status="running",
            started_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            original_execution=original_result,
        )

        if original_result.succeeded:
            state.mark_finished(
                status="no_failure_detected",
                final_message="The provided script already executed successfully.",
            )
            self.logger.write_trace(state, path.stem)
            return state

        current_source = source
        current_result = original_result

        for attempt_index in range(1, self.config.max_attempts + 1):
            diagnosis = self.diagnoser.diagnose(current_source, current_result)
            if not diagnosis.supported:
                state.add_attempt(
                    AttemptRecord(
                        attempt_index=attempt_index,
                        diagnosis=diagnosis,
                        patch_candidate=None,
                        verification=None,
                    )
                )
                state.mark_finished(
                    status="stopped_unsupported",
                    final_message=diagnosis.stop_reason or "Unsupported failure.",
                )
                self.logger.write_trace(state, path.stem)
                return state

            patch_candidate = self.patcher.generate(current_source, diagnosis)
            if patch_candidate is None:
                state.add_attempt(
                    AttemptRecord(
                        attempt_index=attempt_index,
                        diagnosis=diagnosis,
                        patch_candidate=None,
                        verification=None,
                    )
                )
                state.mark_finished(
                    status="stopped_no_patch",
                    final_message="The patcher could not construct a conservative patch.",
                )
                self.logger.write_trace(state, path.stem)
                return state

            verification = self.verifier.verify(
                current_result,
                patch_candidate.patched_source,
                filename=path.name,
            )
            state.add_attempt(
                AttemptRecord(
                    attempt_index=attempt_index,
                    diagnosis=diagnosis,
                    patch_candidate=patch_candidate,
                    verification=verification,
                )
            )

            if verification.success:
                saved_patch = self.logger.write_patch(
                    path.stem,
                    session_id,
                    patch_candidate.patched_source,
                )
                state.mark_finished(
                    status="fixed",
                    final_message="TraceFix produced a verified patch candidate.",
                    saved_patch_path=str(saved_patch),
                )
                self.logger.write_trace(state, path.stem)
                return state

            if verification.failure_kind == "same_failure":
                state.mark_finished(
                    status="stopped_same_failure",
                    final_message="Verification reproduced the same failure after patching.",
                )
                self.logger.write_trace(state, path.stem)
                return state

            current_source = patch_candidate.patched_source
            current_result = verification.execution_result

        state.mark_finished(
            status="max_attempts_reached",
            final_message="Retry budget exhausted before the script executed successfully.",
        )
        self.logger.write_trace(state, path.stem)
        return state
