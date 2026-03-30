from __future__ import annotations

import json
from pathlib import Path

from tracefix.types import VerifierRequest
from tracefix.types import VerifierResult
from tracefix.types import to_dict


class VerifierAgent:
    """Makes a conservative accept/retry/escalate/stop decision for a patch."""

    def __init__(self, prompt_path: str | Path | None = None) -> None:
        self.prompt_path = Path(prompt_path) if prompt_path else (
            Path(__file__).resolve().parents[1] / "prompts" / "verifier_prompt.txt"
        )

    def verify(self, request: VerifierRequest) -> VerifierResult:
        original = request.original_execution_result
        rerun = request.rerun_execution_result
        patch_result = request.patch_result

        regression_flags = self._regression_flags(request)
        behavior_match_status = self._behavior_match_status(request)
        original_failure_resolved = self._original_failure_resolved(original, rerun)
        same_failure = rerun.failure_signature == original.failure_signature
        retries_exhausted = request.retry_count >= request.max_retries
        broad_patch = patch_result is not None and patch_result.minimality_flag == "broad"

        rationale = []
        targeted_feedback: list[str] = []

        if same_failure:
            rationale.append("The rerun reproduced the same failure signature as the original execution.")
            targeted_feedback.append("The previous patch did not change the failing behavior. Change strategy rather than repeating the same edit.")
            if retries_exhausted:
                return VerifierResult(
                    decision="stop",
                    rationale=" ".join(rationale) + " Retry budget is exhausted, so the loop should stop.",
                    regression_flags=regression_flags,
                    behavior_match_status=behavior_match_status,
                    original_failure_resolved=False,
                    uncertainty_notes="No new evidence was produced by the latest patch attempt.",
                    targeted_feedback_for_retry=targeted_feedback,
                )
            return VerifierResult(
                decision="retry",
                rationale=" ".join(rationale) + " A bounded retry is still plausible because the patch can be revised.",
                regression_flags=regression_flags,
                behavior_match_status=behavior_match_status,
                original_failure_resolved=False,
                uncertainty_notes="The original failure still holds, so confidence in the last patch is low.",
                targeted_feedback_for_retry=targeted_feedback,
            )

        if rerun.succeeded:
            if behavior_match_status == "matched_expected_output" and not broad_patch:
                return VerifierResult(
                    decision="accept",
                    rationale="The original failure is gone and the rerun output matches the expected behavior.",
                    regression_flags=regression_flags,
                    behavior_match_status=behavior_match_status,
                    original_failure_resolved=True,
                    uncertainty_notes="Acceptance confidence is strengthened by the explicit output check and a non-broad patch.",
                    targeted_feedback_for_retry=[],
                )

            if behavior_match_status == "mismatched_expected_output":
                rationale.append("The crash was removed, but the observed output does not match the expected behavior.")
                targeted_feedback.append("Adjust the patch toward the expected output rather than only preventing the exception.")
                if retries_exhausted:
                    return VerifierResult(
                        decision="stop",
                        rationale=" ".join(rationale) + " Retry budget is exhausted, so automatic attempts should stop.",
                        regression_flags=regression_flags,
                        behavior_match_status=behavior_match_status,
                        original_failure_resolved=True,
                        uncertainty_notes="Behavioral mismatch remains even though the direct crash was removed.",
                        targeted_feedback_for_retry=targeted_feedback,
                    )
                return VerifierResult(
                    decision="retry",
                    rationale=" ".join(rationale) + " A bounded follow-up patch is plausible because an explicit expected output exists.",
                    regression_flags=regression_flags,
                    behavior_match_status=behavior_match_status,
                    original_failure_resolved=True,
                    uncertainty_notes="The program runs, but behavior still misses the available oracle.",
                    targeted_feedback_for_retry=targeted_feedback,
                )

            rationale.append("The rerun completed without the original failure, but no strong behavior oracle proves correctness.")
            if broad_patch:
                regression_flags.append("broad_patch_requires_review")
                rationale.append("The patch is broad enough that human review is safer than automatic acceptance.")
            else:
                regression_flags.append("no_behavior_oracle")
            return VerifierResult(
                decision="escalate",
                rationale=" ".join(rationale),
                regression_flags=regression_flags,
                behavior_match_status=behavior_match_status,
                original_failure_resolved=True,
                uncertainty_notes="The patch may be correct, but acceptance would risk a false positive without stronger behavioral evidence.",
                targeted_feedback_for_retry=["Add an explicit expected output or stronger test oracle before automatic acceptance."],
            )

        if original_failure_resolved and not retries_exhausted and not broad_patch:
            rationale.append("The original failure signature changed, which suggests partial improvement.")
            rationale.append("The new rerun evidence points to a bounded next step rather than an endless loop.")
            targeted_feedback.append("Use the new rerun failure as the next diagnosis target instead of repeating the previous strategy.")
            return VerifierResult(
                decision="retry",
                rationale=" ".join(rationale),
                regression_flags=regression_flags,
                behavior_match_status=behavior_match_status,
                original_failure_resolved=True,
                uncertainty_notes="The original failure may be resolved, but a new failure now blocks progress.",
                targeted_feedback_for_retry=targeted_feedback,
            )

        if retries_exhausted:
            return VerifierResult(
                decision="stop",
                rationale="The rerun still does not justify acceptance and the retry budget is exhausted.",
                regression_flags=regression_flags,
                behavior_match_status=behavior_match_status,
                original_failure_resolved=original_failure_resolved,
                uncertainty_notes="Further automatic retries risk looping without enough new evidence.",
                targeted_feedback_for_retry=["Escalate to human review with the original and rerun traces."],
            )

        return VerifierResult(
            decision="escalate",
            rationale="The rerun changed behavior, but the remaining evidence is too uncertain for automatic acceptance or another confident retry.",
            regression_flags=regression_flags,
            behavior_match_status=behavior_match_status,
            original_failure_resolved=original_failure_resolved,
            uncertainty_notes="Human judgment is needed because the rerun evidence does not clearly support a single safe next action.",
            targeted_feedback_for_retry=["Review the rerun failure manually before attempting another patch."],
        )

    def build_prompt(self, request: VerifierRequest) -> str:
        template = self.prompt_path.read_text(encoding="utf-8")
        payload = json.dumps(to_dict(request), indent=2, ensure_ascii=False)
        return template.replace("{{INPUT_JSON}}", payload)

    @staticmethod
    def _original_failure_resolved(original, rerun) -> bool:
        return rerun.failure_signature != original.failure_signature

    @staticmethod
    def _behavior_match_status(request: VerifierRequest) -> str:
        rerun = request.rerun_execution_result
        if request.expected_output is not None:
            return (
                "matched_expected_output"
                if rerun.stdout.strip() == request.expected_output.strip()
                else "mismatched_expected_output"
            )
        if request.simple_test_spec is not None and rerun.succeeded:
            return "test_executed_without_explicit_oracle"
        if rerun.succeeded:
            return "no_behavior_oracle"
        return "rerun_failed"

    @staticmethod
    def _regression_flags(request: VerifierRequest) -> list[str]:
        original = request.original_execution_result
        rerun = request.rerun_execution_result
        patch_result = request.patch_result
        flags: list[str] = []

        if rerun.timed_out and not original.timed_out:
            flags.append("timeout_regression")
        if not rerun.succeeded and rerun.failure_signature != original.failure_signature:
            flags.append("new_failure_signature")
        if patch_result is not None and patch_result.minimality_flag == "broad":
            flags.append("broad_patch")
        if request.expected_output is None and rerun.succeeded and original.stdout != rerun.stdout:
            flags.append("stdout_changed_without_oracle")
        if original.return_code == 0 and rerun.return_code != 0:
            flags.append("new_crash_after_patch")

        return flags
