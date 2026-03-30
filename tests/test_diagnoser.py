from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.agents.diagnoser_agent import DiagnoserAgent
from tracefix.types import DiagnoserRequest
from tracefix.types import ExecutionResult


class DiagnoserAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = DiagnoserAgent()

    def test_syntax_case_returns_localized_high_confidence_diagnosis(self) -> None:
        code = "def countdown(start)\n    return start\n"
        result = ExecutionResult(
            command=["python3.11", "target.py"],
            return_code=1,
            stdout="",
            stderr="SyntaxError: invalid syntax",
            timed_out=False,
            duration_ms=10,
            exception_type="SyntaxError",
            exception_message="invalid syntax",
            failure_line=1,
            outcome_label="syntax_error",
        )

        diagnosis = self.agent.diagnose(
            DiagnoserRequest(code=code, latest_execution_result=result)
        )

        self.assertEqual(diagnosis.primary_bug_class, "syntax_error")
        self.assertEqual(diagnosis.localized_code_region.start_line, 1)
        self.assertIn("colon", diagnosis.recommended_repair_direction.lower())
        self.assertEqual(diagnosis.confidence_band, "high")

    def test_name_error_case_returns_typo_hypothesis(self) -> None:
        code = (
            'def greet(name):\n'
            '    messgae = f"Hello, {name}!"\n'
            "    print(message)\n"
        )
        result = ExecutionResult(
            command=["python3.11", "target.py"],
            return_code=1,
            stdout="",
            stderr="NameError: name 'message' is not defined",
            timed_out=False,
            duration_ms=12,
            exception_type="NameError",
            exception_message="name 'message' is not defined",
            failure_line=3,
            outcome_label="runtime_exception",
            traceback_text="Traceback (most recent call last): ...",
        )

        diagnosis = self.agent.diagnose(
            DiagnoserRequest(code=code, latest_execution_result=result)
        )

        self.assertEqual(diagnosis.primary_bug_class, "name_error")
        self.assertEqual(diagnosis.repair_hints["target_name"], "message")
        self.assertEqual(diagnosis.repair_hints["replacement_name"], "messgae")
        self.assertEqual(diagnosis.confidence_band, "high")

    def test_import_case_returns_import_error(self) -> None:
        code = "import not_real_module\nprint('hi')\n"
        result = ExecutionResult(
            command=["python3.11", "target.py"],
            return_code=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'not_real_module'",
            timed_out=False,
            duration_ms=9,
            exception_type="ModuleNotFoundError",
            exception_message="No module named 'not_real_module'",
            failure_line=1,
            outcome_label="missing_file_or_resource",
        )

        diagnosis = self.agent.diagnose(
            DiagnoserRequest(code=code, latest_execution_result=result)
        )

        self.assertEqual(diagnosis.primary_bug_class, "import_error")
        self.assertIn("import", diagnosis.likely_root_cause.lower())
        self.assertIn("not_real_module", "\n".join(diagnosis.evidence_summary))

    def test_file_path_case_returns_missing_resource(self) -> None:
        code = 'open("missing.txt", "r", encoding="utf-8").read()\n'
        result = ExecutionResult(
            command=["python3.11", "target.py"],
            return_code=1,
            stdout="",
            stderr="FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'",
            timed_out=False,
            duration_ms=8,
            exception_type="FileNotFoundError",
            exception_message="[Errno 2] No such file or directory: 'missing.txt'",
            failure_line=1,
            outcome_label="missing_file_or_resource",
        )

        diagnosis = self.agent.diagnose(
            DiagnoserRequest(code=code, latest_execution_result=result)
        )

        self.assertEqual(diagnosis.primary_bug_class, "file_path_or_missing_resource")
        self.assertIn("missing resource", diagnosis.likely_root_cause.lower())
        self.assertEqual(diagnosis.localized_code_region.start_line, 1)

    def test_ambiguous_case_returns_low_confidence_and_alternative(self) -> None:
        code = 'value = 10\nprint(value + " apples")\n'
        result = ExecutionResult(
            command=["python3.11", "target.py"],
            return_code=1,
            stdout="",
            stderr="TypeError: unsupported operand type(s) for +: 'int' and 'str'",
            timed_out=False,
            duration_ms=11,
            exception_type="TypeError",
            exception_message="unsupported operand type(s) for +: 'int' and 'str'",
            failure_line=2,
            outcome_label="runtime_exception",
            traceback_text="Traceback (most recent call last): ...",
        )

        diagnosis = self.agent.diagnose(
            DiagnoserRequest(
                code=code,
                latest_execution_result=result,
                prior_patch_history=["Tried replacing + with f-string formatting but verification failed."],
                prior_verifier_feedback=["Patch changed behavior but still did not satisfy expected output."],
            )
        )

        self.assertEqual(diagnosis.primary_bug_class, "common_runtime_exception")
        self.assertEqual(diagnosis.confidence_band, "low")
        self.assertTrue(diagnosis.alternative_hypotheses)
        self.assertIn("Prior patch history exists", diagnosis.uncertainty_notes)


if __name__ == "__main__":
    unittest.main()
