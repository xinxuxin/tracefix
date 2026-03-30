from __future__ import annotations

import re
from pathlib import Path

from tracefix.types import CodeRegion
from tracefix.types import PatchChangedRegion
from tracefix.types import PatcherRequest
from tracefix.types import PatcherResult
from tracefix.utils.diff_utils import compute_changed_regions
from tracefix.utils.diff_utils import compute_unified_diff


class PatcherAgent:
    """Synthesizes the smallest reasonable code edit from a diagnosis."""

    def __init__(self, prompt_path: str | Path | None = None) -> None:
        self.prompt_path = Path(prompt_path) if prompt_path else (
            Path(__file__).resolve().parents[1] / "prompts" / "patcher_prompt.txt"
        )

    def patch(self, request: PatcherRequest) -> PatcherResult:
        diagnosis = request.diagnosis_result

        if diagnosis.confidence_score < 0.45 and not diagnosis.repair_hints:
            return self._refusal(
                request,
                "Diagnosis confidence is too low for a bounded patch without stronger localized evidence.",
            )

        strategy_id = self._select_strategy(diagnosis)
        if strategy_id is None:
            return self._refusal(
                request,
                "No conservative patch strategy is available for this diagnosis.",
            )

        if self._failed_before(strategy_id, request.prior_patch_history, request.verifier_feedback):
            return self._refusal(
                request,
                "Retry would repeat a previously failed patch strategy without enough new evidence.",
            )

        updated_code = self._apply_strategy(request.code, diagnosis, strategy_id)
        if updated_code is None:
            return self._refusal(
                request,
                "The selected patch strategy could not produce a safe localized edit.",
            )

        safeguard_failure = self._run_safeguards(request.code, updated_code, diagnosis.confidence_score)
        if safeguard_failure is not None:
            return self._refusal(request, safeguard_failure)

        patch_diff = compute_unified_diff(request.code, updated_code)
        changed_regions = compute_changed_regions(request.code, updated_code)
        changed_line_count = sum((region.end_line - region.start_line + 1) for region in changed_regions)
        total_lines = max(1, len(request.code.splitlines()))
        change_ratio = changed_line_count / total_lines
        minimality_flag = self._minimality_flag(changed_line_count, change_ratio)
        confidence_score = max(
            0.2,
            diagnosis.confidence_score - (0.0 if minimality_flag == "minimal" else 0.1 if minimality_flag == "moderate" else 0.25),
        )

        return PatcherResult(
            updated_code=updated_code,
            patch_diff=patch_diff,
            changed_regions=changed_regions,
            patch_summary=self._patch_summary(strategy_id, minimality_flag),
            intended_effect=diagnosis.recommended_repair_direction,
            minimality_flag=minimality_flag,
            confidence_score=confidence_score,
            refusal_reason=None,
            strategy_id=strategy_id,
        )

    def build_prompt(self, request: PatcherRequest) -> str:
        template = self.prompt_path.read_text(encoding="utf-8")
        diagnosis = request.diagnosis_result
        prompt_payload = {
            "user_intent": request.user_intent,
            "prior_patch_history": request.prior_patch_history,
            "verifier_feedback": request.verifier_feedback,
            "diagnosis_summary": {
                "primary_bug_class": diagnosis.primary_bug_class,
                "likely_root_cause": diagnosis.likely_root_cause,
                "localized_code_region": diagnosis.localized_code_region,
                "recommended_repair_direction": diagnosis.recommended_repair_direction,
                "confidence_score": diagnosis.confidence_score,
                "uncertainty_notes": diagnosis.uncertainty_notes,
                "repair_hints": diagnosis.repair_hints,
            },
            "current_code": request.code,
        }
        return template.replace("{{INPUT_JSON}}", str(prompt_payload))

    def _select_strategy(self, diagnosis) -> str | None:
        hints = diagnosis.repair_hints
        if diagnosis.primary_bug_class == "syntax_error" and hints.get("missing_colon"):
            return "append_missing_colon"
        if diagnosis.primary_bug_class == "name_error" and hints.get("replacement_name"):
            return "rename_identifier"
        if diagnosis.primary_bug_class == "argument_mismatch" and hints.get("remove_call_arguments"):
            return "remove_call_arguments"
        if diagnosis.primary_bug_class == "file_path_or_missing_resource" and hints.get("missing_path"):
            return "guard_missing_file_read"
        return None

    def _apply_strategy(self, code: str, diagnosis, strategy_id: str) -> str | None:
        if strategy_id == "append_missing_colon":
            return self._append_missing_colon(code, diagnosis.localized_code_region)
        if strategy_id == "rename_identifier":
            return self._rename_identifier(code, diagnosis.repair_hints)
        if strategy_id == "remove_call_arguments":
            return self._remove_call_arguments(code, diagnosis.localized_code_region)
        if strategy_id == "guard_missing_file_read":
            return self._guard_missing_file_read(code, diagnosis.localized_code_region, diagnosis.repair_hints)
        return None

    def _append_missing_colon(self, code: str, region: CodeRegion) -> str | None:
        if region.start_line is None:
            return None
        lines = code.splitlines()
        index = region.start_line - 1
        if index < 0 or index >= len(lines):
            return None
        if lines[index].rstrip().endswith(":"):
            return None
        lines[index] = lines[index].rstrip() + ":"
        return "\n".join(lines) + "\n"

    def _rename_identifier(self, code: str, repair_hints: dict[str, object]) -> str | None:
        target_name = repair_hints.get("target_name")
        replacement_name = repair_hints.get("replacement_name")
        if not isinstance(target_name, str) or not isinstance(replacement_name, str):
            return None

        pattern = rf"\b{re.escape(target_name)}\b"
        updated_code, replacements = re.subn(pattern, replacement_name, code)
        if replacements == 0:
            return None
        if not updated_code.endswith("\n"):
            updated_code += "\n"
        return updated_code

    def _remove_call_arguments(self, code: str, region: CodeRegion) -> str | None:
        if region.start_line is None:
            return None
        lines = code.splitlines()
        index = region.start_line - 1
        if index < 0 or index >= len(lines):
            return None

        line = lines[index]
        updated_line, replacements = re.subn(r"(\b[A-Za-z_][A-Za-z0-9_]*\s*)\([^()]+\)", r"\1()", line, count=1)
        if replacements == 0:
            return None

        lines[index] = updated_line
        return "\n".join(lines) + "\n"

    def _guard_missing_file_read(
        self,
        code: str,
        region: CodeRegion,
        repair_hints: dict[str, object],
    ) -> str | None:
        if region.start_line is None:
            return None
        missing_path = repair_hints.get("missing_path")
        if not isinstance(missing_path, str):
            return None

        lines = code.splitlines()
        index = region.start_line - 1
        if index < 0 or index >= len(lines):
            return None

        line = lines[index]
        quoted_path = repr(missing_path)

        if "open(" not in line:
            return None

        if "Path(" not in code:
            lines.insert(0, "from pathlib import Path")
            index += 1
            line = lines[index]

        guarded_line = re.sub(
            r"open\([^)]*\)\.read\(\)",
            f'Path({quoted_path}).read_text(encoding="utf-8") if Path({quoted_path}).exists() else ""',
            line,
            count=1,
        )

        if guarded_line == line:
            guarded_line = (
                f'Path({quoted_path}).read_text(encoding="utf-8") '
                f'if Path({quoted_path}).exists() else ""'
            )

        lines[index] = guarded_line
        return "\n".join(lines) + "\n"

    def _run_safeguards(
        self,
        original_code: str,
        updated_code: str,
        diagnosis_confidence: float,
    ) -> str | None:
        if not updated_code.strip():
            return "Patch synthesis produced empty code, which is rejected."

        original_line_count = max(1, len(original_code.splitlines()))
        updated_line_count = len(updated_code.splitlines())
        if updated_line_count < max(1, int(original_line_count * 0.5)):
            return "Patch would massively truncate the script and is rejected."

        changed_regions = compute_changed_regions(original_code, updated_code)
        changed_line_count = sum((region.end_line - region.start_line + 1) for region in changed_regions)
        change_ratio = changed_line_count / original_line_count
        if change_ratio > 0.6 and diagnosis_confidence < 0.8:
            return "Patch would be too broad for the current diagnosis confidence."

        return None

    @staticmethod
    def _minimality_flag(changed_line_count: int, change_ratio: float) -> str:
        if changed_line_count <= 2:
            return "minimal"
        if change_ratio <= 0.15:
            return "minimal"
        if change_ratio <= 0.4:
            return "moderate"
        return "broad"

    @staticmethod
    def _patch_summary(strategy_id: str, minimality_flag: str) -> str:
        return f"Applied {strategy_id} using a {minimality_flag} localized patch."

    @staticmethod
    def _failed_before(
        strategy_id: str,
        prior_patch_history: list[str],
        verifier_feedback: list[str],
    ) -> bool:
        combined_history = " ".join(prior_patch_history + verifier_feedback).lower()
        return strategy_id.replace("_", " ") in combined_history or strategy_id in combined_history

    @staticmethod
    def _refusal(request: PatcherRequest, reason: str) -> PatcherResult:
        return PatcherResult(
            updated_code=request.code,
            patch_diff="",
            changed_regions=[],
            patch_summary="Patch refused",
            intended_effect=request.diagnosis_result.recommended_repair_direction,
            minimality_flag="minimal",
            confidence_score=max(0.1, request.diagnosis_result.confidence_score - 0.3),
            refusal_reason=reason,
            strategy_id=None,
        )
