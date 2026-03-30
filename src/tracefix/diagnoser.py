from __future__ import annotations

from tracefix.agents.diagnoser_agent import DiagnoserAgent
from tracefix.types import DiagnoserRequest
from tracefix.types import Diagnosis
from tracefix.types import ExecutionResult


class Diagnoser:
    """Compatibility wrapper that adapts the richer diagnoser output."""

    def __init__(self, agent: DiagnoserAgent | None = None) -> None:
        self.agent = agent or DiagnoserAgent()

    def diagnose(self, source: str, result: ExecutionResult) -> Diagnosis:
        if result.succeeded:
            return Diagnosis(
                supported=False,
                bug_class="no_failure",
                summary="The script executed successfully.",
                evidence=["The executor returned exit code 0."],
                confidence=1.0,
                stop_reason="no_failure_detected",
            )

        detailed = self.agent.diagnose(
            DiagnoserRequest(
                code=source,
                latest_execution_result=result,
                expected_output=result.expected_output,
                session_state_summary="Controller compatibility path.",
            )
        )

        repair_hints = detailed.repair_hints

        if detailed.primary_bug_class == "syntax_error" and repair_hints.get("missing_colon"):
            return Diagnosis(
                supported=True,
                bug_class="missing_colon",
                summary=detailed.likely_root_cause,
                evidence=detailed.evidence_summary,
                confidence=detailed.confidence_score,
                line_number=repair_hints.get("line_number"),
            )

        if detailed.primary_bug_class == "name_error" and repair_hints.get("replacement_name"):
            return Diagnosis(
                supported=True,
                bug_class="name_error_typo",
                summary=detailed.likely_root_cause,
                evidence=detailed.evidence_summary,
                confidence=detailed.confidence_score,
                line_number=repair_hints.get("line_number"),
                target_name=repair_hints.get("target_name"),
                replacement_name=repair_hints.get("replacement_name"),
            )

        return Diagnosis(
            supported=False,
            bug_class="unsupported_failure",
            summary=detailed.likely_root_cause,
            evidence=detailed.evidence_summary,
            confidence=detailed.confidence_score,
            stop_reason="unsupported_failure",
        )
