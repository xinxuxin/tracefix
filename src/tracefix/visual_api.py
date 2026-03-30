from __future__ import annotations

import csv
import json
import mimetypes
import os
import tempfile
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tracefix.config import TraceFixConfig
from tracefix.orchestrator.controller import TraceFixController
from tracefix.types import to_dict


REPO_ROOT = Path(__file__).resolve().parents[2]


CASE_LIBRARY: dict[str, dict[str, Any]] = {
    "bug_case_01_syntax_error": {
        "title": "Missing Colon",
        "filename": "bug_case_01_syntax_error.py",
        "description": "A function definition is missing a trailing colon on the block opener.",
        "expected_output": "A\n",
        "group": "happy_path",
        "badge": "Syntax demo",
        "recommended_for_video": True,
    },
    "bug_case_02_name_error": {
        "title": "Undefined Variable Typo",
        "filename": "bug_case_02_name_error.py",
        "description": "A runtime name typo is localized and repaired with a small rename.",
        "expected_output": "10.70\n",
        "group": "happy_path",
        "badge": "Best quick demo",
        "recommended_for_video": True,
    },
    "bug_case_03_argument_mismatch": {
        "title": "Argument Mismatch",
        "filename": "bug_case_03_argument_mismatch.py",
        "description": "A function is called with an extra argument, requiring a bounded call-site repair.",
        "expected_output": "TRACEFIX READY\n",
        "group": "happy_path",
        "badge": "Retry-free repair",
        "recommended_for_video": False,
    },
    "bug_case_04_missing_file": {
        "title": "Missing File Guard",
        "filename": "bug_case_04_missing_file.py",
        "description": "A missing resource is handled by a conservative fallback instead of broad rewriting.",
        "expected_output": "Guest\n",
        "group": "happy_path",
        "badge": "Artifact-friendly",
        "recommended_for_video": True,
    },
    "bug_case_05_runtime_exception": {
        "title": "Unsupported Runtime Failure",
        "filename": "bug_case_05_runtime_exception.py",
        "description": "An IndexError remains outside the current bounded patch strategies, so the system stops.",
        "expected_output": None,
        "group": "failure_case",
        "badge": "Conservative stop",
        "recommended_for_video": True,
    },
    "bug_case_06_failure_superficial_fix": {
        "title": "Superficial Fix Failure",
        "filename": "bug_case_06_failure_superficial_fix.py",
        "description": "The crash can disappear while the intended greeting behavior still fails verification.",
        "expected_output": "Hello, TraceFix!\n",
        "group": "governance",
        "badge": "Best failure analysis",
        "recommended_for_video": True,
    },
    "bug_case_07_failure_ambiguous_behavior": {
        "title": "Ambiguous Behavior",
        "filename": "bug_case_07_failure_ambiguous_behavior.py",
        "description": "A local rename can remove the crash, but no oracle exists to justify automatic acceptance.",
        "expected_output": None,
        "group": "governance",
        "badge": "Escalation demo",
        "recommended_for_video": True,
    },
}


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8123
    static_dir: Path | None = None


class TraceFixVisualService:
    """Thin local adapter for the optional frontend demo layer."""

    def __init__(
        self,
        *,
        repo_root: Path = REPO_ROOT,
        outputs_root: Path | None = None,
        evaluation_root: Path | None = None,
        config_path: Path | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.cases_root = repo_root / "cases"
        self.outputs_root = outputs_root or (repo_root / "outputs")
        self.evaluation_root = evaluation_root or (repo_root / "evaluation")
        self.outputs_root.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config(config_path)

    def health(self) -> dict[str, str]:
        return {
            "status": "ok",
            "service": "tracefix-visual-api",
        }

    def list_cases(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for case_id, metadata in CASE_LIBRARY.items():
            path = self.cases_root / metadata["filename"]
            results.append(
                {
                    "caseId": case_id,
                    "title": metadata["title"],
                    "filename": metadata["filename"],
                    "description": metadata["description"],
                    "expectedOutput": metadata["expected_output"],
                    "group": metadata["group"],
                    "badge": metadata["badge"],
                    "recommendedForVideo": metadata["recommended_for_video"],
                    "code": path.read_text(encoding="utf-8"),
                    "path": str(path),
                }
            )
        return results

    def get_latest_session(self) -> dict[str, Any] | None:
        session_root = self.outputs_root / "sessions"
        if not session_root.exists():
            return None
        candidates = [path for path in session_root.iterdir() if path.is_dir()]
        if not candidates:
            return None
        latest_dir = max(candidates, key=lambda item: item.stat().st_mtime)
        state_path = latest_dir / "session_state.json"
        if not state_path.exists():
            return None
        state_payload = json.loads(state_path.read_text(encoding="utf-8"))
        original_code = self._read_original_code_from_state(state_payload)
        return self._build_session_payload_from_saved_state(
            state_payload=state_payload,
            session_dir=latest_dir,
            original_code=original_code,
        )

    def run_debug_session(
        self,
        *,
        code: str,
        filename: str = "workspace_case.py",
        expected_output: str | None = None,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        if not code.strip():
            raise ValueError("Code input cannot be empty.")

        session_root = self.outputs_root / "sessions"
        controller = TraceFixController(
            config=self.config.with_overrides(max_attempts=max_retries),
            session_root=session_root,
        )
        with tempfile.TemporaryDirectory(prefix="tracefix_visual_") as temp_dir:
            script_path = Path(temp_dir) / filename
            script_path.write_text(code, encoding="utf-8")
            state = controller.debug_file(
                script_path,
                expected_output=expected_output,
                max_retries=max_retries,
            )
        if state.session_dir:
            input_copy_path = Path(state.session_dir) / "input_code.py"
            input_copy_path.write_text(code, encoding="utf-8")
        return self._build_session_payload(state=state, original_code=code)

    def get_evaluation_snapshot(self) -> dict[str, Any]:
        latest_run = self._find_latest_evaluation_run()
        planned_rows = self._read_planned_rows()
        if latest_run is None:
            return {
                "latestRunPath": None,
                "summary": None,
                "results": [],
                "failureCases": [],
                "plannedRows": planned_rows,
            }

        results_path = latest_run / "evaluation_results.csv"
        failure_path = latest_run / "failure_cases.csv"
        results = self._read_csv_rows(results_path)
        failures = self._read_csv_rows(failure_path)
        return {
            "latestRunPath": str(latest_run),
            "summary": self._summarize_evaluation_rows(results),
            "results": results,
            "failureCases": failures,
            "plannedRows": planned_rows,
        }

    def _build_session_payload(self, *, state, original_code: str) -> dict[str, Any]:
        state_payload = to_dict(state)
        session_dir = Path(state.session_dir) if state.session_dir else None
        return self._build_session_payload_from_saved_state(
            state_payload=state_payload,
            session_dir=session_dir,
            original_code=original_code,
        )

    def _build_session_payload_from_saved_state(
        self,
        *,
        state_payload: dict[str, Any],
        session_dir: Path | None,
        original_code: str,
    ) -> dict[str, Any]:
        trace_events_path = Path(state_payload["trace_events_path"]) if state_payload.get("trace_events_path") else None
        trace_events = self._read_jsonl(trace_events_path) if trace_events_path else []
        attempt_details = state_payload.get("attempt_details", [])
        last_attempt = attempt_details[-1] if attempt_details else {}
        latest_patch = self._build_latest_patch(last_attempt)
        verifier = self._build_verifier_payload(last_attempt, state_payload)
        artifacts = self._build_artifact_payload(state_payload)
        pipeline = self._build_pipeline_payload(state_payload, last_attempt, verifier)

        return {
            "session": {
                "sessionId": state_payload.get("session_id"),
                "status": state_payload.get("status"),
                "finalDecision": state_payload.get("final_decision"),
                "finalMessage": state_payload.get("final_message"),
                "targetFile": state_payload.get("target_file"),
                "sessionDir": state_payload.get("session_dir"),
                "attemptsUsed": len(state_payload.get("attempts", [])),
                "maxAttempts": state_payload.get("max_attempts"),
                "behaviorMatchStatus": state_payload.get("behavior_match_status"),
                "handoffCount": state_payload.get("handoff_count"),
                "startedAt": state_payload.get("started_at"),
            },
            "overview": {
                "title": "TraceFix",
                "subtitle": "Thin local visualization layer over the existing CLI-first debugging workflow.",
                "targetUser": "Beginner-to-intermediate Python users debugging one small script at a time.",
                "whyAgentic": "Distinct components collect evidence, diagnose, patch, verify, and stop conservatively.",
                "scopedBoundaries": [
                    "Single-file Python only",
                    "No internet access during debugging",
                    "No package installation during debugging",
                    "Bounded retries and conservative escalation",
                ],
            },
            "originalCode": original_code,
            "originalExecution": state_payload.get("original_execution"),
            "latestDiagnosis": last_attempt.get("diagnosis_result"),
            "latestPatch": latest_patch,
            "patchAttempts": self._build_patch_attempts(attempt_details),
            "verifier": verifier,
            "traceEvents": trace_events,
            "pipeline": pipeline,
            "artifacts": artifacts,
            "summaryMarkdown": self._read_text(Path(artifacts["summaryPath"])) if artifacts["summaryPath"] else "",
            "failureSummaryMarkdown": self._read_text(Path(artifacts["failureSummaryPath"])) if artifacts["failureSummaryPath"] else "",
            "finalPatchedCode": self._read_text(Path(artifacts["finalPatchPath"])) if artifacts["finalPatchPath"] else "",
            "sessionDirExists": bool(session_dir and session_dir.exists()),
        }

    def _build_patch_attempts(self, attempt_details: list[dict[str, Any]]) -> list[dict[str, Any]]:
        attempts: list[dict[str, Any]] = []
        for detail in attempt_details:
            patch_path = detail.get("patch_path")
            diff_path = detail.get("diff_path")
            patch_result = detail.get("patch_result") or {}
            attempts.append(
                {
                    "attemptIndex": detail.get("attempt_index"),
                    "strategyId": patch_result.get("strategy_id"),
                    "patchSummary": patch_result.get("patch_summary"),
                    "minimalityFlag": patch_result.get("minimality_flag"),
                    "confidenceScore": patch_result.get("confidence_score"),
                    "refusalReason": patch_result.get("refusal_reason"),
                    "patchPath": patch_path,
                    "diffPath": diff_path,
                    "patchCode": self._read_text(Path(patch_path)) if patch_path else "",
                    "diffText": self._read_text(Path(diff_path)) if diff_path else "",
                }
            )
        return attempts

    def _build_latest_patch(self, last_attempt: dict[str, Any]) -> dict[str, Any] | None:
        if not last_attempt:
            return None
        patch_result = last_attempt.get("patch_result")
        if not patch_result:
            return None
        patch_path = last_attempt.get("patch_path")
        diff_path = last_attempt.get("diff_path")
        return {
            "strategyId": patch_result.get("strategy_id"),
            "patchSummary": patch_result.get("patch_summary"),
            "minimalityFlag": patch_result.get("minimality_flag"),
            "confidenceScore": patch_result.get("confidence_score"),
            "refusalReason": patch_result.get("refusal_reason"),
            "changedRegions": patch_result.get("changed_regions", []),
            "updatedCode": patch_result.get("updated_code", ""),
            "patchDiff": self._read_text(Path(diff_path)) if diff_path else patch_result.get("patch_diff", ""),
            "patchPath": patch_path,
            "diffPath": diff_path,
        }

    def _build_verifier_payload(
        self,
        last_attempt: dict[str, Any],
        state_payload: dict[str, Any],
    ) -> dict[str, Any]:
        verifier = last_attempt.get("verifier_result") if last_attempt else None
        if not verifier:
            return {
                "decision": state_payload.get("final_decision") or "not_run",
                "rationale": state_payload.get("final_message") or "Verifier did not run for this session.",
                "regressionFlags": [],
                "behaviorMatchStatus": state_payload.get("behavior_match_status") or "unknown",
                "originalFailureResolved": False,
                "uncertaintyNotes": "No verifier result is available because patching was refused or no patch was attempted.",
                "targetedFeedbackForRetry": [],
            }
        return {
            "decision": verifier.get("decision"),
            "rationale": verifier.get("rationale"),
            "regressionFlags": verifier.get("regression_flags", []),
            "behaviorMatchStatus": verifier.get("behavior_match_status"),
            "originalFailureResolved": verifier.get("original_failure_resolved"),
            "uncertaintyNotes": verifier.get("uncertainty_notes"),
            "targetedFeedbackForRetry": verifier.get("targeted_feedback_for_retry", []),
        }

    def _build_artifact_payload(self, state_payload: dict[str, Any]) -> dict[str, Any]:
        session_dir = state_payload.get("session_dir")
        return {
            "sessionDir": state_payload.get("session_dir"),
            "summaryPath": state_payload.get("summary_path"),
            "tracePath": state_payload.get("trace_events_path"),
            "stateSnapshotPath": state_payload.get("trace_path"),
            "finalPatchPath": state_payload.get("saved_patch_path"),
            "failureSummaryPath": state_payload.get("failure_summary_path"),
            "intermediatePatchPaths": state_payload.get("intermediate_patch_paths", []),
            "inputCodePath": str(Path(session_dir) / "input_code.py") if session_dir else None,
        }

    def _build_pipeline_payload(
        self,
        state_payload: dict[str, Any],
        last_attempt: dict[str, Any],
        verifier: dict[str, Any],
    ) -> list[dict[str, Any]]:
        final_decision = state_payload.get("final_decision")
        patch_result = last_attempt.get("patch_result") if last_attempt else None
        diagnosis = last_attempt.get("diagnosis_result") if last_attempt else None
        return [
            {
                "id": "controller",
                "label": "Controller",
                "status": self._controller_status(final_decision),
                "detail": f"Attempts used: {len(state_payload.get('attempts', []))}",
            },
            {
                "id": "executor",
                "label": "Executor",
                "status": "success" if state_payload.get("original_execution") else "idle",
                "detail": state_payload.get("original_execution", {}).get("outcome_label", "idle"),
            },
            {
                "id": "diagnoser",
                "label": "Diagnoser",
                "status": "success" if diagnosis else "idle",
                "detail": diagnosis.get("primary_bug_class", "No diagnosis yet") if diagnosis else "No diagnosis yet",
            },
            {
                "id": "patcher",
                "label": "Patcher",
                "status": self._patcher_status(patch_result),
                "detail": patch_result.get("patch_summary", "No patch attempt") if patch_result else "No patch attempt",
            },
            {
                "id": "verifier",
                "label": "Verifier",
                "status": self._verifier_status(verifier.get("decision")),
                "detail": verifier.get("decision", "not_run"),
            },
        ]

    @staticmethod
    def _controller_status(final_decision: str | None) -> str:
        if final_decision == "accept":
            return "success"
        if final_decision == "retry":
            return "retry"
        if final_decision == "escalate":
            return "escalated"
        if final_decision == "stop":
            return "stopped"
        return "idle"

    @staticmethod
    def _patcher_status(patch_result: dict[str, Any] | None) -> str:
        if not patch_result:
            return "idle"
        if patch_result.get("refusal_reason"):
            return "stopped"
        return "success"

    @staticmethod
    def _verifier_status(decision: str | None) -> str:
        if decision == "accept":
            return "success"
        if decision == "retry":
            return "retry"
        if decision == "escalate":
            return "escalated"
        if decision == "stop":
            return "stopped"
        return "idle"

    def _load_config(self, config_path: Path | None) -> TraceFixConfig:
        config = TraceFixConfig.from_env()
        if config_path and config_path.exists():
            return config.merge(TraceFixConfig.from_json(config_path))
        env_config = os.getenv("TRACEFIX_CONFIG")
        if env_config and Path(env_config).exists():
            return config.merge(TraceFixConfig.from_json(env_config))
        default_config = self.repo_root / "config" / "settings.example.json"
        if default_config.exists():
            return config.merge(TraceFixConfig.from_json(default_config))
        return config

    def _read_planned_rows(self) -> list[dict[str, str]]:
        template_path = self.evaluation_root / "results_template.csv"
        if not template_path.exists():
            return []
        return self._read_csv_rows(template_path)

    def _find_latest_evaluation_run(self) -> Path | None:
        runs_root = self.evaluation_root / "runs"
        if not runs_root.exists():
            return None
        candidates = [item for item in runs_root.iterdir() if item.is_dir()]
        if not candidates:
            return None
        return max(candidates, key=lambda item: item.stat().st_mtime)

    @staticmethod
    def _read_csv_rows(path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def _summarize_evaluation_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
        if not rows:
            return {
                "totalCases": 0,
                "accepted": 0,
                "failedOrStopped": 0,
                "escalated": 0,
                "averageRetries": 0,
                "averageLatencyMs": 0,
            }
        accepted = sum(1 for row in rows if row.get("outcome_label") == "accept")
        escalated = sum(1 for row in rows if row.get("outcome_label") == "escalate")
        failed_or_stopped = sum(1 for row in rows if row.get("outcome_label") in {"stop", "max_attempts_reached"})
        retry_values = [int(row["retry_count"]) for row in rows if row.get("retry_count", "").isdigit()]
        latency_values = [int(row["latency_ms"]) for row in rows if row.get("latency_ms", "").isdigit()]
        return {
            "totalCases": len(rows),
            "accepted": accepted,
            "failedOrStopped": failed_or_stopped,
            "escalated": escalated,
            "averageRetries": round(sum(retry_values) / len(retry_values), 2) if retry_values else 0,
            "averageLatencyMs": round(sum(latency_values) / len(latency_values), 2) if latency_values else 0,
        }

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events

    @staticmethod
    def _read_text(path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _read_original_code_from_state(state_payload: dict[str, Any]) -> str:
        target_file = state_payload.get("target_file")
        if target_file:
            path = Path(target_file)
            if path.exists():
                return path.read_text(encoding="utf-8")
        session_dir = state_payload.get("session_dir")
        if session_dir:
            input_copy = Path(session_dir) / "input_code.py"
            if input_copy.exists():
                return input_copy.read_text(encoding="utf-8")
        return ""


class TraceFixVisualRequestHandler(BaseHTTPRequestHandler):
    server: "TraceFixVisualServer"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(self.server.service.health())
            return
        if parsed.path == "/api/cases":
            self._send_json({"cases": self.server.service.list_cases()})
            return
        if parsed.path == "/api/latest-session":
            self._send_json({"session": self.server.service.get_latest_session()})
            return
        if parsed.path == "/api/evaluation":
            self._send_json(self.server.service.get_evaluation_snapshot())
            return
        if self.server.static_dir is not None:
            self._serve_static_asset(parsed.path)
            return
        self._send_json(
            {"error": "Route not found."},
            status=HTTPStatus.NOT_FOUND,
        )

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run":
            self._send_json({"error": "Route not found."}, status=HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        try:
            session = self.server.service.run_debug_session(
                code=str(payload.get("code", "")),
                filename=str(payload.get("filename", "workspace_case.py")),
                expected_output=payload.get("expectedOutput"),
                max_retries=int(payload.get("maxRetries", 2)),
            )
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"session": session})

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _serve_static_asset(self, path: str) -> None:
        assert self.server.static_dir is not None
        requested = path.lstrip("/") or "index.html"
        safe_path = (self.server.static_dir / requested).resolve()
        try:
            safe_path.relative_to(self.server.static_dir.resolve())
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return

        if safe_path.is_dir():
            safe_path = safe_path / "index.html"
        if not safe_path.exists():
            safe_path = self.server.static_dir / "index.html"
        if not safe_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(str(safe_path))
        data = safe_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._send_cors_headers()
        self.send_header("Content-Type", content_type or "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


class TraceFixVisualServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        service: TraceFixVisualService,
        static_dir: Path | None = None,
    ) -> None:
        super().__init__(server_address, TraceFixVisualRequestHandler)
        self.service = service
        self.static_dir = static_dir


def run_visual_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8123,
    static_dir: str | Path | None = None,
    config_path: str | Path | None = None,
) -> None:
    service = TraceFixVisualService(config_path=Path(config_path) if config_path is not None else None)
    resolved_static = Path(static_dir).resolve() if static_dir else None
    server = TraceFixVisualServer((host, port), service=service, static_dir=resolved_static)
    try:
        print(f"TraceFix visual server listening on http://{host}:{port}")
        if resolved_static is not None:
            print(f"Serving frontend assets from: {resolved_static}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
