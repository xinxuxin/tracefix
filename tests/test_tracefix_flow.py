from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.controller import TraceFixController


class TraceFixFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="tracefix_test_")
        self.base = Path(self.temp_dir.name)
        self.trace_dir = self.base / "traces"
        self.patch_dir = self.base / "patches"
        self.controller = TraceFixController(
            max_attempts=2,
            timeout_seconds=2,
            trace_dir=self.trace_dir,
            patch_dir=self.patch_dir,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_name_error_typo_is_fixed(self) -> None:
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

        self.assertEqual(state.status, "fixed")
        self.assertIsNotNone(state.trace_path)
        self.assertIsNotNone(state.saved_patch_path)
        saved_patch = Path(state.saved_patch_path)
        self.assertTrue(saved_patch.exists())
        self.assertIn("print(messgae)", saved_patch.read_text(encoding="utf-8"))

    def test_missing_colon_is_fixed(self) -> None:
        script_path = self.base / "missing_colon_bug.py"
        script_path.write_text(
            (
                "def countdown(start)\n"
                "    while start > 0:\n"
                "        print(start)\n"
                "        start -= 1\n\n"
                "countdown(3)\n"
            ),
            encoding="utf-8",
        )

        state = self.controller.debug_file(
            script_path,
            expected_output="3\n2\n1\n",
        )

        self.assertEqual(state.status, "fixed")
        saved_patch = Path(state.saved_patch_path)
        self.assertIn("def countdown(start):", saved_patch.read_text(encoding="utf-8"))

    def test_unsupported_type_error_stops_conservatively(self) -> None:
        script_path = self.base / "type_error_bug.py"
        script_path.write_text(
            'value = 10\nprint(value + " apples")\n',
            encoding="utf-8",
        )

        state = self.controller.debug_file(script_path)

        self.assertEqual(state.status, "stopped_no_patch")
        self.assertEqual(state.final_decision, "stop")

    def test_trace_file_contains_attempt_history(self) -> None:
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
        trace_payload = json.loads(Path(state.trace_path).read_text(encoding="utf-8"))

        self.assertEqual(trace_payload["status"], "fixed")
        self.assertEqual(len(trace_payload["attempts"]), 1)
        self.assertEqual(
            trace_payload["attempts"][0]["diagnosis"]["bug_class"],
            "name_error_typo",
        )


if __name__ == "__main__":
    unittest.main()
