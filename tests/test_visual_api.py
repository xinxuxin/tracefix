from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.visual_api import REPO_ROOT
from tracefix.visual_api import TraceFixVisualService


class TraceFixVisualServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="tracefix_visual_api_test_")
        self.base = Path(self.temp_dir.name)
        self.outputs_root = self.base / "outputs"
        self.evaluation_root = self.base / "evaluation"
        self.service = TraceFixVisualService(
            repo_root=REPO_ROOT,
            outputs_root=self.outputs_root,
            evaluation_root=self.evaluation_root,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_list_cases_returns_expected_case_groups(self) -> None:
        cases = self.service.list_cases()

        case_ids = {case["caseId"] for case in cases}
        self.assertIn("bug_case_02_name_error", case_ids)
        self.assertIn("bug_case_06_failure_superficial_fix", case_ids)
        self.assertIn("bug_case_07_failure_ambiguous_behavior", case_ids)
        self.assertGreaterEqual(len(cases), 7)

    def test_run_debug_session_returns_rich_session_payload(self) -> None:
        payload = self.service.run_debug_session(
            code=(
                'def greet(name):\n'
                '    messgae = f"Hello, {name}!"\n'
                "    print(message)\n\n"
                'greet("TraceFix")\n'
            ),
            filename="visual_case.py",
            expected_output="Hello, TraceFix!\n",
            max_retries=2,
        )

        self.assertEqual(payload["session"]["finalDecision"], "accept")
        self.assertTrue(payload["traceEvents"])
        self.assertTrue(payload["pipeline"])
        self.assertEqual(payload["verifier"]["decision"], "accept")
        self.assertIn("print(message)", payload["originalCode"])
        self.assertTrue(payload["artifacts"]["inputCodePath"])
        self.assertTrue(Path(payload["artifacts"]["inputCodePath"]).exists())

    def test_evaluation_snapshot_reads_latest_run_outputs(self) -> None:
        run_dir = self.evaluation_root / "runs" / "20260329T120000Z"
        run_dir.mkdir(parents=True, exist_ok=True)

        results_path = run_dir / "evaluation_results.csv"
        failures_path = run_dir / "failure_cases.csv"

        with results_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "case_id",
                    "case_type",
                    "input_or_scenario",
                    "expected_behavior",
                    "ideal_system_action",
                    "judgment_rule",
                    "task_success",
                    "outcome_label",
                    "retry_count",
                    "latency_ms",
                    "patch_breadth",
                    "original_failure_resolved",
                    "behavior_match_status",
                    "evidence_or_citation",
                    "notes",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "case_id": "bug_case_02_name_error",
                    "case_type": "name_error",
                    "input_or_scenario": "undefined variable typo",
                    "expected_behavior": "print 10.70",
                    "ideal_system_action": "accept",
                    "judgment_rule": "accepted patch",
                    "task_success": "yes",
                    "outcome_label": "accept",
                    "retry_count": "1",
                    "latency_ms": "124",
                    "patch_breadth": "minimal",
                    "original_failure_resolved": "True",
                    "behavior_match_status": "matched_expected_output",
                    "evidence_or_citation": "/tmp/example",
                    "notes": "demo",
                }
            )

        with failures_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["case_id", "outcome_label"])
            writer.writeheader()
            writer.writerow({"case_id": "bug_case_06_failure_superficial_fix", "outcome_label": "stop"})

        snapshot = self.service.get_evaluation_snapshot()

        self.assertEqual(snapshot["latestRunPath"], str(run_dir))
        self.assertEqual(snapshot["summary"]["totalCases"], 1)
        self.assertEqual(snapshot["summary"]["accepted"], 1)
        self.assertEqual(snapshot["results"][0]["case_id"], "bug_case_02_name_error")


if __name__ == "__main__":
    unittest.main()
