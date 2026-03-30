from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.agents.verifier_agent import VerifierAgent
from tracefix.types import CodeRegion
from tracefix.types import DiagnoserResult
from tracefix.types import ExecutionResult
from tracefix.types import PatcherResult
from tracefix.types import PatchChangedRegion
from tracefix.types import VerifierRequest


class VerifierAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = VerifierAgent()

    def _base_diagnosis(self) -> DiagnoserResult:
        return DiagnoserResult(
            primary_bug_class="name_error",
            likely_root_cause="An undefined variable name is likely a typo.",
            localized_code_region=CodeRegion(start_line=3, end_line=3, snippet="print(message)"),
            evidence_summary=["NameError raised at line 3."],
            recommended_repair_direction="Replace the undefined identifier with the intended local variable.",
            confidence_score=0.9,
            confidence_band="high",
            uncertainty_notes="",
            repair_hints={"target_name": "message", "replacement_name": "messgae", "line_number": 3},
        )

    def _base_patch(self, minimality_flag: str = "minimal") -> PatcherResult:
        return PatcherResult(
            updated_code='def greet(name):\n    messgae = f"Hello, {name}!"\n    print(messgae)\n',
            patch_diff="@@\n-    print(message)\n+    print(messgae)\n",
            changed_regions=[
                PatchChangedRegion(
                    start_line=3,
                    end_line=3,
                    original_snippet="    print(message)",
                    updated_snippet="    print(messgae)",
                )
            ],
            patch_summary="Applied rename_identifier using a minimal localized patch.",
            intended_effect="Replace the undefined identifier with the intended local variable.",
            minimality_flag=minimality_flag,
            confidence_score=0.9,
            strategy_id="rename_identifier",
        )

    def test_true_success_case_is_accepted(self) -> None:
        original_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=1,
            stdout="",
            stderr="NameError: name 'message' is not defined",
            timed_out=False,
            duration_ms=10,
            exception_type="NameError",
            exception_message="name 'message' is not defined",
            failure_line=3,
            outcome_label="runtime_exception",
        )
        rerun_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=0,
            stdout="Hello, TraceFix!\n",
            stderr="",
            timed_out=False,
            duration_ms=8,
            outcome_label="normal_completion",
        )

        result = self.agent.verify(
            VerifierRequest(
                original_code="print(message)\n",
                patched_code="print(messgae)\n",
                original_execution_result=original_result,
                rerun_execution_result=rerun_result,
                expected_output="Hello, TraceFix!\n",
                diagnosis_result=self._base_diagnosis(),
                patch_result=self._base_patch(),
                retry_count=0,
                max_retries=2,
            )
        )

        self.assertEqual(result.decision, "accept")
        self.assertTrue(result.original_failure_resolved)
        self.assertEqual(result.behavior_match_status, "matched_expected_output")

    def test_crash_removed_but_wrong_behavior_requests_retry(self) -> None:
        original_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=1,
            stdout="",
            stderr="NameError: name 'message' is not defined",
            timed_out=False,
            duration_ms=10,
            exception_type="NameError",
            exception_message="name 'message' is not defined",
            failure_line=3,
            outcome_label="runtime_exception",
        )
        rerun_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=0,
            stdout="Hello, wrong!\n",
            stderr="",
            timed_out=False,
            duration_ms=8,
            outcome_label="normal_completion",
        )

        result = self.agent.verify(
            VerifierRequest(
                original_code="print(message)\n",
                patched_code="print(messgae)\n",
                original_execution_result=original_result,
                rerun_execution_result=rerun_result,
                expected_output="Hello, TraceFix!\n",
                diagnosis_result=self._base_diagnosis(),
                patch_result=self._base_patch(),
                retry_count=0,
                max_retries=2,
            )
        )

        self.assertEqual(result.decision, "retry")
        self.assertTrue(result.original_failure_resolved)
        self.assertEqual(result.behavior_match_status, "mismatched_expected_output")

    def test_partial_improvement_can_retry(self) -> None:
        original_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=1,
            stdout="",
            stderr="NameError: name 'message' is not defined",
            timed_out=False,
            duration_ms=10,
            exception_type="NameError",
            exception_message="name 'message' is not defined",
            failure_line=3,
            outcome_label="runtime_exception",
        )
        rerun_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=1,
            stdout="",
            stderr="FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'",
            timed_out=False,
            duration_ms=9,
            exception_type="FileNotFoundError",
            exception_message="[Errno 2] No such file or directory: 'missing.txt'",
            failure_line=4,
            outcome_label="missing_file_or_resource",
        )

        result = self.agent.verify(
            VerifierRequest(
                original_code="print(message)\n",
                patched_code="print(messgae)\nopen('missing.txt').read()\n",
                original_execution_result=original_result,
                rerun_execution_result=rerun_result,
                diagnosis_result=self._base_diagnosis(),
                patch_result=self._base_patch(),
                retry_count=0,
                max_retries=2,
            )
        )

        self.assertEqual(result.decision, "retry")
        self.assertIn("new_failure_signature", result.regression_flags)
        self.assertTrue(result.original_failure_resolved)

    def test_broad_patch_without_behavior_oracle_escalates(self) -> None:
        original_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=1,
            stdout="",
            stderr="TypeError: unsupported operand type(s)",
            timed_out=False,
            duration_ms=10,
            exception_type="TypeError",
            exception_message="unsupported operand type(s)",
            failure_line=2,
            outcome_label="runtime_exception",
        )
        rerun_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=0,
            stdout="patched output\n",
            stderr="",
            timed_out=False,
            duration_ms=7,
            outcome_label="normal_completion",
        )

        result = self.agent.verify(
            VerifierRequest(
                original_code='print(value + " apples")\n',
                patched_code='print("patched output")\n',
                original_execution_result=original_result,
                rerun_execution_result=rerun_result,
                diagnosis_result=self._base_diagnosis(),
                patch_result=self._base_patch(minimality_flag="broad"),
                retry_count=0,
                max_retries=2,
            )
        )

        self.assertEqual(result.decision, "escalate")
        self.assertIn("broad_patch", result.regression_flags)

    def test_same_failure_stops_after_max_retries(self) -> None:
        original_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=1,
            stdout="",
            stderr="NameError: name 'message' is not defined",
            timed_out=False,
            duration_ms=10,
            exception_type="NameError",
            exception_message="name 'message' is not defined",
            failure_line=3,
            outcome_label="runtime_exception",
        )
        rerun_result = ExecutionResult(
            command=["python3.11", "case.py"],
            return_code=1,
            stdout="",
            stderr="NameError: name 'message' is not defined",
            timed_out=False,
            duration_ms=9,
            exception_type="NameError",
            exception_message="name 'message' is not defined",
            failure_line=3,
            outcome_label="runtime_exception",
        )

        result = self.agent.verify(
            VerifierRequest(
                original_code="print(message)\n",
                patched_code="print(message)\n",
                original_execution_result=original_result,
                rerun_execution_result=rerun_result,
                diagnosis_result=self._base_diagnosis(),
                patch_result=self._base_patch(),
                retry_count=2,
                max_retries=2,
            )
        )

        self.assertEqual(result.decision, "stop")
        self.assertFalse(result.original_failure_resolved)


if __name__ == "__main__":
    unittest.main()
