from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.agents.patcher_agent import PatcherAgent
from tracefix.types import CodeRegion
from tracefix.types import DiagnoserResult
from tracefix.types import PatcherRequest


class PatcherAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = PatcherAgent()

    def test_syntax_repair_appends_missing_colon(self) -> None:
        code = "def countdown(start)\n    return start\n"
        diagnosis = DiagnoserResult(
            primary_bug_class="syntax_error",
            likely_root_cause="A block-opening statement is likely missing a trailing colon.",
            localized_code_region=CodeRegion(start_line=1, end_line=1, snippet="def countdown(start)"),
            evidence_summary=["Line 1 is missing a trailing colon."],
            recommended_repair_direction="Add the missing colon on the localized block header and rerun.",
            confidence_score=0.96,
            confidence_band="high",
            uncertainty_notes="",
            repair_hints={"missing_colon": True, "line_number": 1},
        )

        patch = self.agent.patch(PatcherRequest(code=code, diagnosis_result=diagnosis))

        self.assertIsNone(patch.refusal_reason)
        self.assertIn("def countdown(start):", patch.updated_code)
        self.assertIn("+def countdown(start):", patch.patch_diff)
        self.assertEqual(patch.minimality_flag, "minimal")

    def test_name_error_repair_renames_identifier(self) -> None:
        code = (
            'def greet(name):\n'
            '    messgae = f"Hello, {name}!"\n'
            "    print(message)\n"
        )
        diagnosis = DiagnoserResult(
            primary_bug_class="name_error",
            likely_root_cause="The undefined name 'message' is likely a typo for the existing identifier 'messgae'.",
            localized_code_region=CodeRegion(start_line=3, end_line=3, snippet="    print(message)"),
            evidence_summary=["Undefined symbol: message", "Closest existing identifier: messgae"],
            recommended_repair_direction="Replace 'message' with 'messgae' in the localized statement.",
            confidence_score=0.9,
            confidence_band="high",
            uncertainty_notes="",
            repair_hints={"target_name": "message", "replacement_name": "messgae", "line_number": 3},
        )

        patch = self.agent.patch(PatcherRequest(code=code, diagnosis_result=diagnosis))

        self.assertIsNone(patch.refusal_reason)
        self.assertIn("print(messgae)", patch.updated_code)
        self.assertTrue(patch.changed_regions)

    def test_argument_mismatch_repair_removes_extra_arguments(self) -> None:
        code = 'def greet():\n    print("hi")\n\ngreet("TraceFix")\n'
        diagnosis = DiagnoserResult(
            primary_bug_class="argument_mismatch",
            likely_root_cause="A function or callable is being invoked with the wrong number of arguments.",
            localized_code_region=CodeRegion(start_line=4, end_line=4, snippet='greet("TraceFix")'),
            evidence_summary=["TypeError indicates too many positional arguments were given."],
            recommended_repair_direction="Match the call site to the function signature.",
            confidence_score=0.86,
            confidence_band="high",
            uncertainty_notes="",
            repair_hints={"remove_call_arguments": True, "line_number": 4},
        )

        patch = self.agent.patch(PatcherRequest(code=code, diagnosis_result=diagnosis))

        self.assertIsNone(patch.refusal_reason)
        self.assertIn("greet()", patch.updated_code)
        self.assertNotIn('greet("TraceFix")', patch.updated_code)

    def test_file_path_guard_adds_path_exists_check(self) -> None:
        code = 'data = open("missing.txt", "r", encoding="utf-8").read()\nprint(data)\n'
        diagnosis = DiagnoserResult(
            primary_bug_class="file_path_or_missing_resource",
            likely_root_cause="The code tries to read a missing resource or file.",
            localized_code_region=CodeRegion(
                start_line=1,
                end_line=1,
                snippet='data = open("missing.txt", "r", encoding="utf-8").read()',
            ),
            evidence_summary=["FileNotFoundError indicates 'missing.txt' does not exist."],
            recommended_repair_direction="Guard the file read so missing resources are handled conservatively.",
            confidence_score=0.82,
            confidence_band="high",
            uncertainty_notes="",
            repair_hints={"missing_path": "missing.txt", "line_number": 1},
        )

        patch = self.agent.patch(PatcherRequest(code=code, diagnosis_result=diagnosis))

        self.assertIsNone(patch.refusal_reason)
        self.assertIn("Path('missing.txt').exists()", patch.updated_code)
        self.assertIn("from pathlib import Path", patch.updated_code)

    def test_broad_or_uncertain_patch_is_refused(self) -> None:
        code = 'value = 10\nprint(value + " apples")\n'
        diagnosis = DiagnoserResult(
            primary_bug_class="common_runtime_exception",
            likely_root_cause="Execution evidence shows a runtime failure, but it does not support a narrow repair hypothesis yet.",
            localized_code_region=CodeRegion(start_line=2, end_line=2, snippet='print(value + " apples")'),
            evidence_summary=["TypeError occurred at line 2."],
            recommended_repair_direction="Inspect the localized statement before attempting a patch.",
            confidence_score=0.3,
            confidence_band="low",
            uncertainty_notes="The root cause may be upstream.",
            repair_hints={},
        )

        patch = self.agent.patch(
            PatcherRequest(
                code=code,
                diagnosis_result=diagnosis,
                prior_patch_history=["rename_identifier failed earlier"],
                verifier_feedback=["Previous patch did not resolve the issue."],
            )
        )

        self.assertIsNotNone(patch.refusal_reason)
        self.assertEqual(patch.updated_code, code)
        self.assertEqual(patch.patch_diff, "")


if __name__ == "__main__":
    unittest.main()
