from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.run_evaluation import run_selected_cases


class EvaluationRunnerTests(unittest.TestCase):
    def test_runner_writes_results_and_failure_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="tracefix_eval_test_") as temp_dir:
            output_dir = Path(temp_dir) / "evaluation_run"
            rows = run_selected_cases(
                case_ids=[
                    "bug_case_02_name_error",
                    "bug_case_05_runtime_exception",
                    "bug_case_07_failure_ambiguous_behavior",
                ],
                output_dir=output_dir,
            )

            self.assertEqual(len(rows), 3)

            results_path = output_dir / "evaluation_results.csv"
            failure_path = output_dir / "failure_cases.csv"
            summary_path = output_dir / "run_summary.md"

            self.assertTrue(results_path.exists())
            self.assertTrue(failure_path.exists())
            self.assertTrue(summary_path.exists())

            with results_path.open(encoding="utf-8", newline="") as handle:
                result_rows = list(csv.DictReader(handle))
            with failure_path.open(encoding="utf-8", newline="") as handle:
                failure_rows = list(csv.DictReader(handle))

            self.assertEqual(len(result_rows), 3)
            self.assertEqual(len(failure_rows), 2)

            outcome_by_case = {row["case_id"]: row["outcome_label"] for row in result_rows}
            self.assertEqual(outcome_by_case["bug_case_02_name_error"], "accept")
            self.assertEqual(outcome_by_case["bug_case_05_runtime_exception"], "stop")
            self.assertEqual(outcome_by_case["bug_case_07_failure_ambiguous_behavior"], "escalate")

            failure_case_ids = {row["case_id"] for row in failure_rows}
            self.assertIn("bug_case_05_runtime_exception", failure_case_ids)
            self.assertIn("bug_case_07_failure_ambiguous_behavior", failure_case_ids)


if __name__ == "__main__":
    unittest.main()
