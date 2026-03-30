from __future__ import annotations

from tracefix.agents.patcher_agent import PatcherAgent
from tracefix.types import CodeRegion
from tracefix.types import Diagnosis
from tracefix.types import DiagnoserResult
from tracefix.types import PatchCandidate
from tracefix.types import PatcherRequest


class Patcher:
    """Compatibility wrapper around the richer patcher agent."""

    def __init__(self, agent: PatcherAgent | None = None) -> None:
        self.agent = agent or PatcherAgent()

    def generate(self, source: str, diagnosis: Diagnosis) -> PatchCandidate | None:
        if not diagnosis.supported:
            return None

        detailed_diagnosis = self._to_diagnoser_result(source, diagnosis)
        result = self.agent.patch(
            PatcherRequest(
                code=source,
                diagnosis_result=detailed_diagnosis,
            )
        )

        if result.refusal_reason:
            return None

        return PatchCandidate(
            strategy=result.strategy_id or "bounded_patch",
            rationale=result.intended_effect,
            patched_source=result.updated_code,
            changed_lines=[region.start_line for region in result.changed_regions],
        )

    def _to_diagnoser_result(self, source: str, diagnosis: Diagnosis) -> DiagnoserResult:
        localized_region = CodeRegion(
            start_line=diagnosis.line_number,
            end_line=diagnosis.line_number,
            snippet=self._line_snippet(source, diagnosis.line_number),
        )
        repair_hints: dict[str, object] = {}

        if diagnosis.bug_class == "missing_colon":
            primary_bug_class = "syntax_error"
            repair_hints["missing_colon"] = True
            repair_hints["line_number"] = diagnosis.line_number
            recommended = "Add the missing colon to the localized block-opening line."
        elif diagnosis.bug_class == "name_error_typo":
            primary_bug_class = "name_error"
            repair_hints["target_name"] = diagnosis.target_name
            repair_hints["replacement_name"] = diagnosis.replacement_name
            repair_hints["line_number"] = diagnosis.line_number
            recommended = "Replace the undefined identifier with the intended in-scope name."
        else:
            primary_bug_class = "common_runtime_exception"
            recommended = "Apply a conservative localized patch only if the edit is well supported."

        return DiagnoserResult(
            primary_bug_class=primary_bug_class,
            likely_root_cause=diagnosis.summary,
            localized_code_region=localized_region,
            evidence_summary=diagnosis.evidence,
            recommended_repair_direction=recommended,
            confidence_score=diagnosis.confidence,
            confidence_band=self._confidence_band(diagnosis.confidence),
            uncertainty_notes=diagnosis.stop_reason or "",
            repair_hints=repair_hints,
        )

    @staticmethod
    def _line_snippet(source: str, line_number: int | None) -> str:
        if line_number is None:
            return ""
        lines = source.splitlines()
        if line_number < 1 or line_number > len(lines):
            return ""
        return lines[line_number - 1]

    @staticmethod
    def _confidence_band(confidence: float) -> str:
        if confidence >= 0.8:
            return "high"
        if confidence >= 0.55:
            return "medium"
        return "low"
