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
    "actual_behavior",
    "ideal_system_action",
    "judgment_rule",
    "task_success",
    "outcome_label",
    "final_decision",
    "retry_count",
    "latency_seconds",
    "patch_breadth",
    "original_failure_resolved",
    "behavior_match_status",
    "evidence_or_citation",
    "trace_path",
    "session_state_path",
    "summary_path",
    "notes",
]

TEST_CASE_COLUMNS = [
    "case_id",
    "filename",
    "case_type",
    "input_or_scenario",
    "expected_behavior",
    "ideal_system_action",
    "expected_final_decision",
    "expected_output",
    "judgment_rule",
    "notes",
]

BASELINE_COLUMNS = [
    "case_id",
    "baseline_name",
    "baseline_outcome",
    "tracefix_outcome",
    "baseline_failure_mode",
    "tracefix_decision",
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
    baseline_rows: list[dict[str, str]] = []

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
        last_patch = _latest_detail_value(state.attempt_details, "patch_result")
        last_verifier = _latest_detail_value(state.attempt_details, "verifier_result")
        last_rerun = _latest_detail_value(state.attempt_details, "rerun_execution_result")
        patch_breadth = getattr(last_patch, "minimality_flag", "none")
        original_failure_resolved = getattr(last_verifier, "original_failure_resolved", False)
        behavior_match_status = state.behavior_match_status or getattr(last_verifier, "behavior_match_status", "n/a")
        task_success = "yes" if state.final_decision == case.expected_final_decision else "no"
        final_decision = state.final_decision or state.status
        actual_behavior = _actual_behavior(state.status, final_decision, last_rerun)
        latency_seconds = f"{latency_ms / 1000:.3f}"
        trace_path = _repo_relative(state.trace_events_path)
        session_state_path = _repo_relative(state.trace_path)
        summary_path = _repo_relative(state.summary_path)

        row = {
            "case_id": case.case_id,
            "case_type": case.case_type,
            "input_or_scenario": case.input_or_scenario,
            "expected_behavior": case.expected_behavior,
            "actual_behavior": actual_behavior,
            "ideal_system_action": case.ideal_system_action,
            "judgment_rule": case.judgment_rule,
            "task_success": task_success,
            "outcome_label": state.final_decision or state.status,
            "final_decision": final_decision,
            "retry_count": str(len(state.attempt_details)),
            "latency_seconds": latency_seconds,
            "patch_breadth": patch_breadth,
            "original_failure_resolved": str(bool(original_failure_resolved)),
            "behavior_match_status": behavior_match_status or "n/a",
            "evidence_or_citation": summary_path or trace_path or session_state_path,
            "trace_path": trace_path,
            "session_state_path": session_state_path,
            "summary_path": summary_path,
            "notes": case.notes,
        }
        rows.append(row)
        baseline_rows.append(_baseline_row(case, state, last_rerun))

        if state.final_decision != "accept":
            failure_rows.append(row)

    _write_test_cases(output_dir / "test_cases.csv", selected_ids)
    _write_csv(output_dir / "evaluation_results.csv", rows)
    _write_csv(output_dir / "failure_cases.csv", failure_rows)
    _write_failure_log(output_dir / "failure_log.md", failure_rows)
    _write_baseline_csv(output_dir / "baseline_comparison.csv", baseline_rows)
    _write_run_summary(output_dir / "run_summary.md", rows)
    _write_version_notes(output_dir / "version_notes.md", output_dir)
    if _should_refresh_root_files(output_dir=output_dir, selected_ids=selected_ids):
        _write_root_evaluation_files(
            rows=rows,
            failure_rows=failure_rows,
            baseline_rows=baseline_rows,
            selected_ids=selected_ids,
            output_dir=output_dir,
        )
    return rows


def _write_csv(destination: Path, rows: list[dict[str, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_test_cases(destination: Path, selected_ids: list[str]) -> None:
    rows = []
    for case_id in selected_ids:
        case = CASE_SPECS[case_id]
        rows.append(
            {
                "case_id": case.case_id,
                "filename": case.filename,
                "case_type": case.case_type,
                "input_or_scenario": case.input_or_scenario,
                "expected_behavior": case.expected_behavior,
                "ideal_system_action": case.ideal_system_action,
                "expected_final_decision": case.expected_final_decision,
                "expected_output": (case.expected_output or "").replace("\n", "\\n"),
                "judgment_rule": case.judgment_rule,
                "notes": case.notes,
            }
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEST_CASE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_baseline_csv(destination: Path, rows: list[dict[str, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASELINE_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_run_summary(destination: Path, rows: list[dict[str, str]]) -> None:
    total = len(rows)
    accepted = sum(1 for row in rows if row["outcome_label"] == "accept")
    stopped = sum(1 for row in rows if row["outcome_label"] == "stop")
    escalated = sum(1 for row in rows if row["outcome_label"] == "escalate")
    task_success = sum(1 for row in rows if row["task_success"] == "yes")
    unresolved = total - accepted
    lines = [
        "# Evaluation Run Summary",
        "",
        f"- Total cases: {total}",
        f"- Accepted cases: {accepted}",
        f"- Stopped cases: {stopped}",
        f"- Escalated cases: {escalated}",
        f"- Unresolved or governed cases: {unresolved}",
        f"- Cases matching expected final decision: {task_success}",
        "",
        "## Case Outcomes",
        "",
    ]
    for row in rows:
        lines.append(
            f"- `{row['case_id']}`: outcome=`{row['outcome_label']}`, "
            f"task_success=`{row['task_success']}`, retries=`{row['retry_count']}`, "
            f"patch_breadth=`{row['patch_breadth']}`, evidence=`{row['summary_path']}`"
        )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_failure_log(destination: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Failure and Governance Log",
        "",
        "This log is generated from executed TraceFix evaluation cases. It includes unresolved, stopped, and escalated cases rather than invented examples.",
        "",
    ]
    if not rows:
        lines.append("No failure or governance cases were produced in this run.")
    for index, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"## failure_{index:02d}: {row['case_id']}",
                "",
                f"- Failure ID: `failure_{index:02d}`",
                f"- Case ID: `{row['case_id']}`",
                f"- What triggered the problem: {row['input_or_scenario']}",
                f"- Expected behavior: {row['expected_behavior']}",
                f"- Actual behavior: {row['actual_behavior']}",
                f"- System decision: `{row['final_decision']}`",
                f"- Why verifier accepted/rejected/escalated/stopped: {row['judgment_rule']}",
                f"- Root cause: {row['notes']}",
                f"- Evidence artifacts: `{row['summary_path']}`, `{row['trace_path']}`, `{row['session_state_path']}`",
                "- What changed after testing: The case was retained as evidence for conservative stopping/escalation and documented in Phase 3 materials.",
                "- Current status: Documented boundary case for final submission.",
                "",
            ]
        )
    destination.write_text("\n".join(lines), encoding="utf-8")


def _write_version_notes(destination: Path, output_dir: Path) -> None:
    lines = [
        "# Evaluation Version Notes",
        "",
        f"- Generated at: {datetime.utcnow().isoformat(timespec='seconds')}Z",
        "- Evaluation mode: local deterministic TraceFix mode",
        "- Provider mode: local unless the caller explicitly exported provider environment variables before running this script",
        "- Baseline mode: deterministic crash-only acceptance baseline",
        f"- Run artifact directory: `{_repo_relative(output_dir)}`",
        "- Notes: Results are produced by executing the repository evaluation runner, not hand-filled.",
        "",
        "## Configuration Snapshot",
        "",
        "- Max attempts per case: 2",
        "- Executor timeout per run: 2 seconds",
        "- Default provider mode in checked-in config: local",
        "- OpenAI default model if enabled: gpt-4.1",
        "- Anthropic default model if enabled: claude-3-5-sonnet-latest",
        "- API temperature if enabled: 0.0",
        "- API max tokens if enabled: 1200",
    ]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_root_evaluation_files(
    *,
    rows: list[dict[str, str]],
    failure_rows: list[dict[str, str]],
    baseline_rows: list[dict[str, str]],
    selected_ids: list[str],
    output_dir: Path,
) -> None:
    evaluation_root = ROOT / "evaluation"
    _write_test_cases(evaluation_root / "test_cases.csv", selected_ids)
    _write_csv(evaluation_root / "evaluation_results.csv", rows)
    _write_csv(evaluation_root / "failure_cases.csv", failure_rows)
    _write_failure_log(evaluation_root / "failure_log.md", failure_rows)
    _write_baseline_csv(evaluation_root / "baseline_comparison.csv", baseline_rows)
    _write_run_summary(evaluation_root / "summary.md", rows)
    _write_version_notes(evaluation_root / "version_notes.md", output_dir)


def _actual_behavior(status: str, final_decision: str, rerun_result) -> str:
    if rerun_result is None:
        return f"Session ended with status={status}, decision={final_decision}, and no patch rerun."
    stdout = getattr(rerun_result, "stdout", "").strip()
    exception = getattr(rerun_result, "exception_type", None)
    outcome = getattr(rerun_result, "outcome_label", "unknown")
    if stdout:
        return f"Session ended with decision={final_decision}; latest rerun outcome={outcome}; stdout={stdout!r}."
    if exception:
        return f"Session ended with decision={final_decision}; latest rerun outcome={outcome}; exception={exception}."
    return f"Session ended with decision={final_decision}; latest rerun outcome={outcome}."


def _latest_detail_value(attempt_details: list[dict[str, object]], key: str):
    for detail in reversed(attempt_details):
        value = detail.get(key) if isinstance(detail, dict) else None
        if value is not None:
            return value
    return None


def _repo_relative(value: str | Path | None) -> str:
    if value is None:
        return ""
    path = Path(value)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _should_refresh_root_files(*, output_dir: Path, selected_ids: list[str]) -> bool:
    """Only full official evaluation runs should update root-level Phase 3 CSVs."""
    if selected_ids != list(CASE_SPECS.keys()):
        return False
    try:
        output_dir.resolve().relative_to((ROOT / "evaluation" / "runs").resolve())
    except ValueError:
        return False
    return True


def _baseline_row(case: EvaluationCase, state, rerun_result) -> dict[str, str]:
    baseline_name = "deterministic_crash_only_acceptance"
    if rerun_result is not None and getattr(rerun_result, "succeeded", False):
        baseline_outcome = "accept"
    else:
        baseline_outcome = "stop"

    tracefix_decision = state.final_decision or state.status
    if baseline_outcome == "accept" and tracefix_decision != "accept":
        failure_mode = "false_positive_acceptance_risk"
    elif baseline_outcome != tracefix_decision:
        failure_mode = "decision_mismatch"
    else:
        failure_mode = "same_decision"

    return {
        "case_id": case.case_id,
        "baseline_name": baseline_name,
        "baseline_outcome": baseline_outcome,
        "tracefix_outcome": tracefix_decision,
        "baseline_failure_mode": failure_mode,
        "tracefix_decision": tracefix_decision,
        "notes": "Baseline accepts any non-crashing patched rerun and does not use expected-output or no-oracle verification.",
    }


if __name__ == "__main__":
    raise SystemExit(main())
