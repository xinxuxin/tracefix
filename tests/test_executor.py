from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.agents.executor_agent import ExecutorAgent
from tracefix.sandbox.executor import Executor
from tracefix.types import ExecutionConfig
from tracefix.types import SessionMetadata
from tracefix.types import SimpleTestSpec


class ExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="tracefix_executor_test_")
        self.base = Path(self.temp_dir.name)
        self.trace_path = self.base / "logs" / "execution_events.jsonl"
        self.config = ExecutionConfig(
            timeout_seconds=1,
            filename="case.py",
            trace_log_path=self.trace_path,
            interpreter_command=(sys.executable,),
        )
        self.executor = Executor(
            timeout_seconds=1,
            trace_log_path=self.trace_path,
            interpreter_command=(sys.executable,),
        )
        self.agent = ExecutorAgent(self.executor)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_successful_script_returns_normal_completion(self) -> None:
        result = self.agent.run(
            code='print("hello tracefix")\n',
            session_metadata=SessionMetadata(session_id="success-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "normal_completion")
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout.strip(), "hello tracefix")
        self.assertFalse(result.timed_out)
        self.assertTrue(self.trace_path.exists())

    def test_syntax_error_script_returns_syntax_error(self) -> None:
        result = self.agent.run(
            code="def broken()\n    pass\n",
            session_metadata=SessionMetadata(session_id="syntax-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "syntax_error")
        self.assertEqual(result.exception_type, "SyntaxError")
        self.assertIn("SyntaxError", result.stderr)

    def test_runtime_exception_script_returns_runtime_exception(self) -> None:
        result = self.agent.run(
            code='raise ValueError("boom")\n',
            session_metadata=SessionMetadata(session_id="runtime-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "runtime_exception")
        self.assertEqual(result.exception_type, "ValueError")
        self.assertIsNotNone(result.traceback_text)
        self.assertIn("ValueError: boom", result.traceback_text)

    def test_timeout_script_returns_timeout(self) -> None:
        result = self.agent.run(
            code="while True:\n    pass\n",
            session_metadata=SessionMetadata(session_id="timeout-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "timeout")
        self.assertTrue(result.timed_out)
        self.assertEqual(result.exception_type, "TimeoutError")

    def test_missing_file_script_returns_missing_file_or_resource(self) -> None:
        result = self.agent.run(
            code='open("missing.txt", "r", encoding="utf-8").read()\n',
            session_metadata=SessionMetadata(session_id="missing-file-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "missing_file_or_resource")
        self.assertEqual(result.exception_type, "FileNotFoundError")

    def test_policy_blocked_script_returns_blocked_by_policy(self) -> None:
        result = self.agent.run(
            code="import socket\nprint('blocked')\n",
            session_metadata=SessionMetadata(session_id="policy-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "blocked_by_policy")
        self.assertEqual(result.exception_type, "PolicyBlocked")
        self.assertIn("Network access", result.stderr)

    def test_simple_test_spec_arguments_are_forwarded(self) -> None:
        result = self.agent.run(
            code="import sys\nprint(sys.argv[1])\n",
            simple_test_spec=SimpleTestSpec(description="argv smoke test", arguments=["hello"]),
            session_metadata=SessionMetadata(session_id="argv-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "normal_completion")
        self.assertEqual(result.stdout.strip(), "hello")

    def test_trace_events_include_start_and_end(self) -> None:
        result = self.agent.run(
            code='print("trace event")\n',
            session_metadata=SessionMetadata(session_id="event-case"),
            execution_config=self.config,
        )

        self.assertEqual(result.outcome_label, "normal_completion")
        lines = self.trace_path.read_text(encoding="utf-8").strip().splitlines()
        events = [json.loads(line) for line in lines]
        self.assertEqual(events[0]["event"], "execution_start")
        self.assertEqual(events[-1]["event"], "execution_end")
        self.assertEqual(events[-1]["outcome_label"], "normal_completion")


if __name__ == "__main__":
    unittest.main()
