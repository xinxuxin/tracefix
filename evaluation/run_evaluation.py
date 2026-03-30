from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tracefix.orchestrator.controller import TraceFixController


RESULT_COLUMNS = [
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
]


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    filename: str
    case_type: str
    input_or_scenario: str
    expected_behavior: str
    ideal_system_action: str
    judgment_rule: str
    expected_final_decision: str
    expected_output: str | None = None
    notes: str = ""


CASE_SPECS: dict[str, EvaluationCase] = {
    "bug_case_01_syntax_error": EvaluationCase(
        case_id="bug_case_01_syntax_error",
        filename="bug_case_01_syntax_error.py",
        case_type="syntax_error",
        input_or_scenario="Function definition is missing a trailing colon.",
        expected_behavior="Print A",
        ideal_system_action="accept",
        judgment_rule="Accepted patch and expected output matched.",
        expected_final_decision="accept",
        expected_output="A\n",
        notes="Minimal syntax repair case.",
    ),
    "bug_case_02_name_error": EvaluationCase(
        case_id="bug_case_02_name_error",
        filename="bug_case_02_name_error.py",
        case_type="name_error",
        input_or_scenario="Formatted total references an undefined variable name.",
        expected_behavior="Print 10.70",
        ideal_system_action="accept",
        judgment_rule="Accepted patch and expected output matched.",
        expected_final_decision="accept",
        expected_output="10.70\n",
        notes="Localized runtime typo repair.",
    ),
    "bug_case_03_argument_mismatch": EvaluationCase(
        case_id="bug_case_03_argument_mismatch",
        filename="bug_case_03_argument_mismatch.py",
        case_type="argument_mismatch",
        input_or_scenario="Function is called with an extra positional argument.",
        expected_behavior="Print TRACEFIX READY",
        ideal_system_action="accept",
        judgment_rule="Accepted patch and expected output matched.",
        expected_final_decision="accept",
        expected_output="TRACEFIX READY\n",
        notes="Call-site repair case.",
    ),
    "bug_case_04_missing_file": EvaluationCase(
        case_id="bug_case_04_missing_file",
        filename="bug_case_04_missing_file.py",
        case_type="file_path_or_missing_resource",
        input_or_scenario="The script reads username.txt, which is not present in the run directory.",
        expected_behavior="Print Guest",
        ideal_system_action="accept",
        judgment_rule="Accepted patch and expected output matched.",
        expected_final_decision="accept",
        expected_output="Guest\n",
        notes="Conservative missing-file guard case.",
    ),
    "bug_case_05_runtime_exception": EvaluationCase(
        case_id="bug_case_05_runtime_exception",
        filename="bug_case_05_runtime_exception.py",
        case_type="common_runtime_exception",
        input_or_scenario="List access raises IndexError with no safe bounded patch strategy.",
        expected_behavior="Stop conservatively instead of over-editing.",
        ideal_system_action="stop",
        judgment_rule="No accepted patch and explicit stop recorded.",
        expected_final_decision="stop",
        notes="Primary unsupported runtime case.",
    ),
    "bug_case_06_failure_superficial_fix": EvaluationCase(
        case_id="bug_case_06_failure_superficial_fix",
        filename="bug_case_06_failure_superficial_fix.py",
        case_type="failure_superficial_fix",
        input_or_scenario="A rename removes the crash, but the remaining output still violates the intended greeting format.",
        expected_behavior="Print Hello, TraceFix!",
        ideal_system_action="stop",
        judgment_rule="Verifier should reject superficial success and session should remain unresolved.",
        expected_final_decision="stop",
        expected_output="Hello, TraceFix!\n",
        notes="Best failure-analysis case for false-positive acceptance risk.",
    ),
    "bug_case_07_failure_ambiguous_behavior": EvaluationCase(
        case_id="bug_case_07_failure_ambiguous_behavior",
        filename="bug_case_07_failure_ambiguous_behavior.py",
        case_type="failure_ambiguous_behavior",
        input_or_scenario="A rename can remove the crash, but no expected output is supplied to verify the intended behavior.",
        expected_behavior="Do not auto-accept without an explicit oracle.",
        ideal_system_action="escalate",
        judgment_rule="Escalated session with no behavior oracle.",
        expected_final_decision="escalate",
        notes="Best governance and ambiguity case.",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the TraceFix evaluation suite.")
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        help="Run only the selected case id. May be provided multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for evaluation artifacts. Defaults to evaluation/runs/<timestamp>/.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else (
        ROOT / "evaluation" / "runs" / datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    )
    run_selected_cases(
        case_ids=args.case_ids,
        output_dir=output_dir,
    )
    print(f"evaluation_output_dir: {output_dir}")
    print(f"results_csv: {output_dir / 'evaluation_results.csv'}")
    print(f"failure_cases_csv: {output_dir / 'failure_cases.csv'}")
    return 0


def run_selected_cases(
    *,
    case_ids: list[str] | None = None,
    output_dir: str | Path,
    case_root: str | Path | None = None,
) -> list[dict[str, str]]:
    selected_ids = case_ids or list(CASE_SPECS.keys())
    output_dir = Path(output_dir)
    case_root = Path(case_root) if case_root is not None else (ROOT / "cases")
    output_dir.mkdir(parents=True, exist_ok=True)
    case_artifact_root = output_dir / "cases"
    case_artifact_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    failure_rows: list[dict[str, str]] = []

    for case_id in selected_ids:
        case = CASE_SPECS[case_id]
        case_output_dir = case_artifact_root / case.case_id
        case_output_dir.mkdir(parents=True, exist_ok=True)

        controller = TraceFixController(
            max_attempts=2,
            timeout_seconds=2,
            trace_dir=case_output_dir / "traces",
            patch_dir=case_output_dir / "patches",
            session_root=case_output_dir / "sessions",
        )
        start = time.perf_counter()
        state = controller.debug_file(
            case_root / case.filename,
            expected_output=case.expected_output,
            max_retries=2,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        last_attempt = state.attempt_details[-1] if state.attempt_details else {}
        last_patch = last_attempt.get("patch_result") if isinstance(last_attempt, dict) else None
        last_verifier = last_attempt.get("verifier_result") if isinstance(last_attempt, dict) else None
        patch_breadth = getattr(last_patch, "minimality_flag", "none")
        original_failure_resolved = getattr(last_verifier, "original_failure_resolved", False)
        behavior_match_status = state.behavior_match_status or getattr(last_verifier, "behavior_match_status", "n/a")
        task_success = "yes" if state.final_decision == case.expected_final_decision else "no"

        row = {
            "case_id": case.case_id,
            "case_type": case.case_type,
            "input_or_scenario": case.input_or_scenario,
            "expected_behavior": case.expected_behavior,
            "ideal_system_action": case.ideal_system_action,
            "judgment_rule": case.judgment_rule,
            "task_success": task_success,
            "outcome_label": state.final_decision or state.status,
            "retry_count": str(len(state.attempt_details)),
            "latency_ms": str(latency_ms),
            "patch_breadth": patch_breadth,
            "original_failure_resolved": str(bool(original_failure_resolved)),
            "behavior_match_status": behavior_match_status or "n/a",
            "evidence_or_citation": state.summary_path or state.trace_path or "",
            "notes": case.notes,
        }
        rows.append(row)

        if state.final_decision != "accept":
            failure_rows.append(row)

    _write_csv(output_dir / "evaluation_results.csv", rows)
    _write_csv(output_dir / "failure_cases.csv", failure_rows)
    _write_run_summary(output_dir / "run_summary.md", rows)
    return rows


def _write_csv(destination: Path, rows: list[dict[str, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_run_summary(destination: Path, rows: list[dict[str, str]]) -> None:
    total = len(rows)
    accepted = sum(1 for row in rows if row["outcome_label"] == "accept")
    unresolved = total - accepted
    lines = [
        "# Evaluation Run Summary",
        "",
        f"- Total cases: {total}",
        f"- Accepted cases: {accepted}",
        f"- Unresolved or governed cases: {unresolved}",
        "",
        "## Case Outcomes",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['case_id']}`: outcome=`{row['outcome_label']}`, "
            f"task_success=`{row['task_success']}`, retries=`{row['retry_count']}`, "
            f"patch_breadth=`{row['patch_breadth']}`"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
