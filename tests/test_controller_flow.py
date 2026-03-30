from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.orchestrator.controller import TraceFixController


class TraceFixControllerFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="tracefix_controller_test_")
        self.base = Path(self.temp_dir.name)
        self.trace_dir = self.base / "traces"
        self.patch_dir = self.base / "patches"
        self.session_root = self.base / "sessions"
        self.controller = TraceFixController(
            max_attempts=2,
            timeout_seconds=1,
            trace_dir=self.trace_dir,
            patch_dir=self.patch_dir,
            session_root=self.session_root,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_successful_end_to_end_case(self) -> None:
        script_path = self.base / "name_error_bug.py"
        script_path.write_text(
            (
                'def greet(name):\n'
                '    messgae = f"Hello, {name}!"\n'
                "    print(message)\n\n"
                'greet("TraceFix")\n'
            ),
            encoding="utf-8",
        )

        state = self.controller.debug_file(
            script_path,
            expected_output="Hello, TraceFix!\n",
        )

        self.assertEqual(state.final_decision, "accept")
        self.assertEqual(state.status, "fixed")
        self.assertTrue(Path(state.saved_patch_path).exists())
        self.assertTrue(Path(state.trace_events_path).exists())
        self.assertTrue(Path(state.summary_path).exists())

    def test_unresolved_case_writes_failure_summary_and_stops(self) -> None:
        script_path = self.base / "type_error_bug.py"
        script_path.write_text(
            'value = 10\nprint(value + " apples")\n',
            encoding="utf-8",
        )

        state = self.controller.debug_file(script_path, max_retries=1)

        self.assertEqual(state.final_decision, "stop")
        self.assertEqual(state.status, "stopped_no_patch")
        self.assertIsNotNone(state.failure_summary_path)
        self.assertTrue(Path(state.failure_summary_path).exists())

    def test_retry_path_reaches_second_attempt_and_accepts(self) -> None:
        script_path = self.base / "retry_case.py"
        script_path.write_text(
            (
                'def greet(name):\n'
                '    messgae = f"Hello, {name}!"\n'
                "    print(message)\n"
                '    data = open("missing.txt", "r", encoding="utf-8").read()\n'
                "    print(data)\n\n"
                'greet("TraceFix")\n'
            ),
            encoding="utf-8",
        )

        state = self.controller.debug_file(
            script_path,
            expected_output="Hello, TraceFix!\n\n",
            max_retries=2,
        )

        self.assertEqual(state.final_decision, "accept")
        self.assertEqual(len(state.attempt_details), 2)
        self.assertEqual(len(state.intermediate_patch_paths), 2)
        trace_lines = Path(state.trace_events_path).read_text(encoding="utf-8").splitlines()
        handoffs = [
            json.loads(line)["handoff"]
            for line in trace_lines
            if '"event": "handoff"' in line
        ]
        self.assertIn("controller -> executor", handoffs)
        self.assertIn("executor -> diagnoser", handoffs)
        self.assertIn("diagnoser -> patcher", handoffs)
        self.assertIn("patcher -> executor", handoffs)
        self.assertIn("executor -> verifier", handoffs)
        self.assertIn("verifier -> controller", handoffs)


if __name__ == "__main__":
    unittest.main()
