from __future__ import annotations

from tracefix.sandbox.executor import Executor
from tracefix.types import ExecutionConfig
from tracefix.types import ExecutionRequest
from tracefix.types import ExecutionResult
from tracefix.types import SessionMetadata
from tracefix.types import SimpleTestSpec


class ExecutorAgent:
    """Thin agent wrapper around the bounded executor component."""

    def __init__(self, executor: Executor | None = None) -> None:
        self.executor = executor or Executor()

    def run(
        self,
        *,
        code: str,
        user_intent: str | None = None,
        expected_output: str | None = None,
        simple_test_spec: SimpleTestSpec | None = None,
        session_metadata: SessionMetadata | None = None,
        execution_config: ExecutionConfig | None = None,
    ) -> ExecutionResult:
        request = ExecutionRequest(
            code=code,
            user_intent=user_intent,
            expected_output=expected_output,
            simple_test_spec=simple_test_spec,
            session_metadata=session_metadata
            or SessionMetadata(session_id="executor-agent-session"),
            execution_config=execution_config or ExecutionConfig(),
        )
        return self.executor.execute(request)
