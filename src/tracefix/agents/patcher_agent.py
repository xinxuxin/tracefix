from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tracefix.config import TraceFixConfig
from tracefix.providers.base import LLMProvider
from tracefix.providers.base import ProviderError
from tracefix.providers.factory import resolve_provider
from tracefix.types import CodeRegion
from tracefix.types import PatchChangedRegion
from tracefix.types import PatcherRequest
from tracefix.types import PatcherResult
from tracefix.types import to_dict
from tracefix.utils.diff_utils import compute_changed_regions
from tracefix.utils.diff_utils import compute_unified_diff


class PatcherAgent:
    """Synthesizes the smallest reasonable code edit from a diagnosis."""

    def __init__(
        self,
        prompt_path: str | Path | None = None,
        *,
        config: TraceFixConfig | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self.prompt_path = Path(prompt_path) if prompt_path else (
            Path(__file__).resolve().parents[1] / "prompts" / "patcher_prompt.txt"
        )
        self.config = config or TraceFixConfig.from_env()
        self.provider = provider

    def patch(self, request: PatcherRequest) -> PatcherResult:
        local_result = self._patch_local(request)
        local_result = self._annotate_result(local_result, execution_mode="local")

        if not self.config.enable_llm_patcher:
            return local_result

        resolution = resolve_provider(self.config, component_name="patcher")
        active_provider = self.provider or resolution.provider
        provider_name = self.provider.provider_name if self.provider is not None else resolution.provider_name
        model_name = self.provider.model_name if self.provider is not None else resolution.model_name

        if active_provider is None:
            return self._annotate_result(
                local_result,
                execution_mode="local",
                provider_name=provider_name,
                model_name=model_name,
                fallback_used=bool(provider_name or resolution.error),
                provider_error=resolution.error,
            )

        try:
            prompt = self.build_prompt(request)
            generation = active_provider.generate_json(
                prompt,
                timeout_seconds=self.config.api_timeout_seconds,
                max_tokens=self.config.api_max_tokens,
            )
            provider_result = self._coerce_provider_result(generation.payload, request, local_result)
            if provider_result.refusal_reason and local_result.refusal_reason is None:
                raise ProviderError(
                    f"Provider returned a refusal while a safe local patch existed: {provider_result.refusal_reason}"
                )
            return self._annotate_result(
                provider_result,
                execution_mode=active_provider.provider_name,
                provider_name=active_provider.provider_name,
                model_name=active_provider.model_name,
            )
        except ProviderError as exc:
            if not self.config.fallback_to_local_on_provider_error:
                raise
            return self._annotate_result(
                local_result,
                execution_mode="local",
                provider_name=provider_name or getattr(active_provider, "provider_name", None),
                model_name=model_name or getattr(active_provider, "model_name", None),
                fallback_used=True,
                provider_error=str(exc),
            )

    def build_prompt(self, request: PatcherRequest) -> str:
        template = self.prompt_path.read_text(encoding="utf-8")
        prompt_payload = {
            "request": to_dict(request),
        }
        return template.replace("{{INPUT_JSON}}", json.dumps(prompt_payload, indent=2, ensure_ascii=False))

    def _patch_local(self, request: PatcherRequest) -> PatcherResult:
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

        return self._build_patch_result(
            original_code=request.code,
            updated_code=updated_code,
            patch_summary="",
            intended_effect=diagnosis.recommended_repair_direction,
            confidence_score=max(0.2, diagnosis.confidence_score),
            strategy_id=strategy_id,
        )

    def _coerce_provider_result(
        self,
        payload: dict[str, Any],
        request: PatcherRequest,
        local_result: PatcherResult,
    ) -> PatcherResult:
        refusal_reason = payload.get("refusal_reason")
        if refusal_reason:
            return self._refusal(request, str(refusal_reason))

        updated_code = payload.get("updated_code")
        if not isinstance(updated_code, str) or not updated_code.strip():
            raise ProviderError("Provider patch output did not include usable updated_code.")

        if updated_code == request.code:
            raise ProviderError("Provider patch output returned unchanged code.")

        safeguard_failure = self._run_safeguards(
            request.code,
            updated_code,
            request.diagnosis_result.confidence_score,
        )
        if safeguard_failure is not None:
            raise ProviderError(safeguard_failure)

        strategy_id = str(payload.get("strategy_id") or local_result.strategy_id or "llm_patch")
        patch_summary = str(
            payload.get("patch_summary") or f"Applied {strategy_id} using a provider-suggested bounded patch."
        )
        intended_effect = str(
            payload.get("intended_effect") or request.diagnosis_result.recommended_repair_direction
        )
        confidence_score = self._coerce_float(payload.get("confidence_score"), local_result.confidence_score)

        return self._build_patch_result(
            original_code=request.code,
            updated_code=updated_code,
            patch_summary=patch_summary,
            intended_effect=intended_effect,
            confidence_score=confidence_score,
            strategy_id=strategy_id,
        )

    @staticmethod
    def _annotate_result(
        result: PatcherResult,
        *,
        execution_mode: str,
        provider_name: str | None = None,
        model_name: str | None = None,
        fallback_used: bool = False,
        provider_error: str | None = None,
    ) -> PatcherResult:
        result.execution_mode = execution_mode
        result.provider_name = provider_name
        result.model_name = model_name
        result.fallback_used = fallback_used
        result.provider_error = provider_error
        return result

    def _build_patch_result(
        self,
        *,
        original_code: str,
        updated_code: str,
        patch_summary: str,
        intended_effect: str,
        confidence_score: float,
        strategy_id: str,
    ) -> PatcherResult:
        patch_diff = compute_unified_diff(original_code, updated_code)
        changed_regions = compute_changed_regions(original_code, updated_code)
        changed_line_count = sum((region.end_line - region.start_line + 1) for region in changed_regions)
        total_lines = max(1, len(original_code.splitlines()))
        change_ratio = changed_line_count / total_lines
        minimality_flag = self._minimality_flag(changed_line_count, change_ratio)
        final_confidence = max(
            0.2,
            confidence_score - (0.0 if minimality_flag == "minimal" else 0.1 if minimality_flag == "moderate" else 0.25),
        )

        return PatcherResult(
            updated_code=updated_code,
            patch_diff=patch_diff,
            changed_regions=changed_regions,
            patch_summary=(
                patch_summary
                if patch_summary and not patch_summary.startswith("Applied ")
                else self._patch_summary(strategy_id, minimality_flag)
            ),
            intended_effect=intended_effect,
            minimality_flag=minimality_flag,
            confidence_score=final_confidence,
            refusal_reason=None,
            strategy_id=strategy_id,
        )

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
        if changed_line_count == 0:
            return "Patch output did not change the script."
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
    def _patch_summary(strategy_id: str, minimality_flag: str | None) -> str:
        if minimality_flag:
            return f"Applied {strategy_id} using a {minimality_flag} localized patch."
        return f"Applied {strategy_id} using a localized patch."

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

    @staticmethod
    def _coerce_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
