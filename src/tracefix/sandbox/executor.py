from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from tracefix.sandbox.policy import PolicyDecision
from tracefix.sandbox.policy import SandboxPolicy
from tracefix.types import ExecutionConfig
from tracefix.types import ExecutionRequest
from tracefix.types import ExecutionResult
from tracefix.types import SessionMetadata
from tracefix.types import to_dict


class Executor:
    """Runs a single Python file in a bounded subprocess and records evidence."""

    def __init__(
        self,
        timeout_seconds: int = 2,
        policy: SandboxPolicy | None = None,
        trace_log_path: str | Path = "logs/traces/execution_events.jsonl",
        interpreter_command: tuple[str, ...] | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.policy = policy or SandboxPolicy()
        self.default_trace_log_path = Path(trace_log_path)
        self.default_interpreter_command = interpreter_command or ("python3.11",)

    def run_source(self, source: str, filename: str = "target.py") -> ExecutionResult:
        """Compatibility wrapper used by the existing controller/verifier path."""

        request = ExecutionRequest(
            code=source,
            session_metadata=SessionMetadata(session_id="controller-execution"),
            execution_config=ExecutionConfig(
                timeout_seconds=self.timeout_seconds,
                filename=filename,
                trace_log_path=self.default_trace_log_path,
                interpreter_command=self.default_interpreter_command,
            ),
        )
        return self.execute(request)

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        config = request.execution_config
        session = request.session_metadata
        policy_decision = self.policy.evaluate(request.code)
        interpreter = self._resolve_interpreter(config.interpreter_command)

        if not policy_decision.allowed:
            result = self._build_policy_blocked_result(
                request=request,
                policy_decision=policy_decision,
            )
            self._write_execution_event(
                config.trace_log_path,
                {
                    "event": "execution_blocked",
                    "timestamp": self._utc_timestamp(),
                    "session_id": session.session_id,
                    "target_file": session.target_file,
                    "outcome_label": result.outcome_label,
                    "blocked_reason": result.blocked_reason,
                },
            )
            return result

        if interpreter is None:
            result = ExecutionResult(
                command=list(config.interpreter_command),
                return_code=127,
                stdout="",
                stderr="Python 3.11 interpreter was not found in the current environment.",
                timed_out=False,
                duration_ms=0,
                exception_type="EnvironmentError",
                exception_message="Python 3.11 interpreter unavailable.",
                outcome_label="unsupported_environment",
                session_id=session.session_id,
                blocked_reason=None,
                policy_notes=policy_decision.notes,
                expected_output=request.expected_output,
            )
            self._write_execution_event(
                config.trace_log_path,
                {
                    "event": "execution_end",
                    "timestamp": self._utc_timestamp(),
                    "session_id": session.session_id,
                    "target_file": session.target_file,
                    "outcome_label": result.outcome_label,
                    "duration_ms": result.duration_ms,
                    "temp_file_path": None,
                    "used_interpreter": None,
                },
            )
            return result

        with tempfile.TemporaryDirectory(prefix=config.temp_dir_prefix) as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_file_path = temp_dir_path / config.filename
            temp_file_path.write_text(request.code, encoding="utf-8")
            command = self._build_command(interpreter, config, request)

            start_time = time.perf_counter()
            self._write_execution_event(
                config.trace_log_path,
                {
                    "event": "execution_start",
                    "timestamp": self._utc_timestamp(),
                    "session_id": session.session_id,
                    "target_file": session.target_file,
                    "temp_file_path": str(temp_file_path),
                    "used_interpreter": interpreter,
                    "timeout_seconds": config.timeout_seconds,
                },
            )

            try:
                completed = subprocess.run(
                    command,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout_seconds,
                    env={"PYTHONIOENCODING": "utf-8"},
                )
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                exception_type, exception_message, failure_line = self._parse_failure(
                    completed.stderr
                )
                result = ExecutionResult(
                    command=command,
                    return_code=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    timed_out=False,
                    duration_ms=duration_ms,
                    exception_type=exception_type,
                    exception_message=exception_message,
                    failure_line=failure_line,
                    outcome_label=self._classify_outcome(
                        return_code=completed.returncode,
                        exception_type=exception_type,
                        exception_message=exception_message,
                    ),
                    traceback_text=self._extract_traceback(completed.stderr),
                    temp_file_path=str(temp_file_path),
                    session_id=session.session_id,
                    used_interpreter=interpreter,
                    policy_notes=policy_decision.notes,
                    expected_output=request.expected_output,
                )
            except subprocess.TimeoutExpired as exc:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                result = ExecutionResult(
                    command=command,
                    return_code=124,
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                    timed_out=True,
                    duration_ms=duration_ms,
                    exception_type="TimeoutError",
                    exception_message=f"Execution exceeded {config.timeout_seconds} seconds.",
                    outcome_label="timeout",
                    traceback_text=self._extract_traceback(exc.stderr or ""),
                    temp_file_path=str(temp_file_path),
                    session_id=session.session_id,
                    used_interpreter=interpreter,
                    policy_notes=policy_decision.notes,
                    expected_output=request.expected_output,
                )
            except OSError as exc:
                result = ExecutionResult(
                    command=command,
                    return_code=127,
                    stdout="",
                    stderr=str(exc),
                    timed_out=False,
                    duration_ms=0,
                    exception_type=type(exc).__name__,
                    exception_message=str(exc),
                    outcome_label="unsupported_environment",
                    temp_file_path=str(temp_file_path),
                    session_id=session.session_id,
                    used_interpreter=interpreter,
                    policy_notes=policy_decision.notes,
                    expected_output=request.expected_output,
                )

            self._write_execution_event(
                config.trace_log_path,
                {
                    "event": "execution_end",
                    "timestamp": self._utc_timestamp(),
                    "session_id": session.session_id,
                    "target_file": session.target_file,
                    "temp_file_path": result.temp_file_path,
                    "used_interpreter": result.used_interpreter,
                    "duration_ms": result.duration_ms,
                    "outcome_label": result.outcome_label,
                    "exit_code": result.return_code,
                    "timed_out": result.timed_out,
                },
            )
            return result

    def _build_policy_blocked_result(
        self,
        request: ExecutionRequest,
        policy_decision: PolicyDecision,
    ) -> ExecutionResult:
        config = request.execution_config
        return ExecutionResult(
            command=list(config.interpreter_command),
            return_code=126,
            stdout="",
            stderr=policy_decision.reason,
            timed_out=False,
            duration_ms=0,
            exception_type="PolicyBlocked",
            exception_message=policy_decision.reason,
            outcome_label="blocked_by_policy",
            session_id=request.session_metadata.session_id,
            blocked_reason=policy_decision.reason,
            policy_notes=policy_decision.notes,
            expected_output=request.expected_output,
        )

    def _build_command(
        self,
        interpreter: str,
        config: ExecutionConfig,
        request: ExecutionRequest,
    ) -> list[str]:
        command = [interpreter]
        if config.isolated_mode:
            command.append("-I")
        if config.bytecode_writes_disabled:
            command.append("-B")
        command.append(config.filename)
        if request.simple_test_spec is not None:
            command.extend(request.simple_test_spec.arguments)
        return command

    @staticmethod
    def _resolve_interpreter(interpreter_command: tuple[str, ...]) -> str | None:
        for candidate in interpreter_command:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
            candidate_path = Path(candidate)
            if candidate_path.exists():
                return str(candidate_path)
        return None

    @staticmethod
    def _parse_failure(stderr: str) -> tuple[str | None, str | None, int | None]:
        if not stderr.strip():
            return None, None, None

        failure_line = None
        line_match = re.findall(r'File ".*?", line (\d+)', stderr)
        if line_match:
            failure_line = int(line_match[-1])

        last_line = stderr.strip().splitlines()[-1]
        if ": " in last_line:
            exception_type, exception_message = last_line.split(": ", 1)
            return exception_type.strip(), exception_message.strip(), failure_line
        return last_line.strip(), "", failure_line

    @staticmethod
    def _extract_traceback(stderr: str) -> str | None:
        if "Traceback (most recent call last):" in stderr:
            return stderr
        return None

    @staticmethod
    def _classify_outcome(
        return_code: int,
        exception_type: str | None,
        exception_message: str | None,
    ) -> str:
        if return_code == 0:
            return "normal_completion"
        if exception_type == "SyntaxError":
            return "syntax_error"
        if exception_type in {"FileNotFoundError", "ModuleNotFoundError"}:
            return "missing_file_or_resource"
        if exception_message and "No such file or directory" in exception_message:
            return "missing_file_or_resource"
        return "runtime_exception"

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    @staticmethod
    def _write_execution_event(trace_log_path: str | Path, event: dict[str, object]) -> None:
        path = Path(trace_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(to_dict(event), ensure_ascii=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")
