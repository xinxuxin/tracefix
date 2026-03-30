from __future__ import annotations

import ast
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from tracefix.types import AlternativeHypothesis
from tracefix.types import CodeRegion
from tracefix.types import DiagnoserRequest
from tracefix.types import DiagnoserResult
from tracefix.types import ExecutionResult
from tracefix.types import to_dict


@dataclass
class _IdentifierCollector(ast.NodeVisitor):
    names: set[str]

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.names.add(node.id)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        self.names.add(node.arg)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name)


class DiagnoserAgent:
    """Interprets execution evidence into a bounded repair hypothesis."""

    CONTROL_PREFIXES = (
        "if ",
        "elif ",
        "else",
        "for ",
        "while ",
        "def ",
        "class ",
        "try",
        "except",
        "with ",
    )

    def __init__(self, prompt_path: str | Path | None = None) -> None:
        self.prompt_path = Path(prompt_path) if prompt_path else (
            Path(__file__).resolve().parents[1] / "prompts" / "diagnoser_prompt.txt"
        )

    def diagnose(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result

        if result.outcome_label == "syntax_error" or result.exception_type == "SyntaxError":
            diagnosis = self._diagnose_syntax_error(request)
        elif result.exception_type == "NameError":
            diagnosis = self._diagnose_name_error(request)
        elif result.exception_type in {"ModuleNotFoundError", "ImportError"}:
            diagnosis = self._diagnose_import_error(request)
        elif result.exception_type == "FileNotFoundError":
            diagnosis = self._diagnose_missing_resource(request)
        elif result.exception_type == "TypeError":
            diagnosis = self._diagnose_type_error(request)
        elif result.succeeded and request.expected_output is not None:
            diagnosis = self._diagnose_output_mismatch(request)
        else:
            diagnosis = self._diagnose_generic_runtime_exception(request)

        if request.prior_patch_history or request.prior_verifier_feedback:
            diagnosis.uncertainty_notes = self._merge_uncertainty_with_history(
                diagnosis.uncertainty_notes,
                request.prior_patch_history,
                request.prior_verifier_feedback,
            )

        diagnosis.alternative_hypotheses = diagnosis.alternative_hypotheses[:2]
        return diagnosis

    def build_prompt(self, request: DiagnoserRequest) -> str:
        template = self.prompt_path.read_text(encoding="utf-8")
        payload = json.dumps(to_dict(request), indent=2, ensure_ascii=False)
        return template.replace("{{INPUT_JSON}}", payload)

    def _diagnose_syntax_error(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result
        region = self._localized_region(request.code, result.failure_line)
        repair_hints: dict[str, object] = {}
        likely_root_cause = "The script contains invalid Python syntax near the reported line."
        recommended = "Inspect the localized line and correct the syntax before changing unrelated code."
        evidence = self._base_evidence(result, region)
        confidence = 0.82
        uncertainty = "Syntax errors are localized well, but the exact token mistake may still require inspection of nearby code."
        alternatives: list[AlternativeHypothesis] = []

        if region.snippet.strip().startswith(self.CONTROL_PREFIXES) and not region.snippet.rstrip().endswith(":"):
            likely_root_cause = "A block-opening statement is likely missing a trailing colon."
            recommended = "Add the missing colon on the localized block header and rerun."
            confidence = 0.96
            repair_hints["missing_colon"] = True
            repair_hints["line_number"] = result.failure_line
            alternatives.append(
                AlternativeHypothesis(
                    bug_class="syntax_error",
                    reason="If the colon is already intended, the line may still contain another malformed token.",
                    confidence_band="low",
                )
            )
        else:
            alternatives.append(
                AlternativeHypothesis(
                    bug_class="syntax_error",
                    reason="The localized line may contain an unmatched delimiter or malformed expression rather than a missing colon.",
                    confidence_band="medium",
                )
            )

        return DiagnoserResult(
            primary_bug_class="syntax_error",
            likely_root_cause=likely_root_cause,
            localized_code_region=region,
            evidence_summary=evidence,
            recommended_repair_direction=recommended,
            confidence_score=confidence,
            confidence_band=self._confidence_band(confidence),
            uncertainty_notes=uncertainty,
            alternative_hypotheses=alternatives,
            direct_cause=result.exception_message,
            downstream_symptom="Python stopped before runtime execution could begin.",
            repair_hints=repair_hints,
        )

    def _diagnose_name_error(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result
        region = self._localized_region(request.code, result.failure_line)
        evidence = self._base_evidence(result, region)
        missing_name = self._extract_name_error_symbol(result)
        replacement = self._closest_known_identifier(request.code, missing_name) if missing_name else None
        repair_hints: dict[str, object] = {"line_number": result.failure_line}
        confidence = 0.72
        likely_root_cause = "A name is being referenced that is not defined in the current single file."
        recommended = "Define the missing name earlier in the file or replace the reference with the intended in-scope identifier."
        uncertainty = "The execution evidence identifies the undefined symbol, but intent is uncertain if several similarly named variables exist."
        alternatives: list[AlternativeHypothesis] = []

        if missing_name:
            repair_hints["target_name"] = missing_name
            evidence.append(f"Undefined symbol from execution result: {missing_name}")

        if replacement:
            repair_hints["replacement_name"] = replacement
            confidence = 0.9
            likely_root_cause = (
                f"The undefined name '{missing_name}' is likely a typo for the existing identifier '{replacement}'."
            )
            recommended = f"Replace '{missing_name}' with '{replacement}' in the localized statement."
            alternatives.append(
                AlternativeHypothesis(
                    bug_class="name_error",
                    reason="The name may instead be intended as a new variable that should be defined before use.",
                    confidence_band="low",
                )
            )
        else:
            alternatives.append(
                AlternativeHypothesis(
                    bug_class="import_or_name_error",
                    reason="The missing name could be an omitted import or helper that is absent from this single-file scope.",
                    confidence_band="medium",
                )
            )

        return DiagnoserResult(
            primary_bug_class="name_error",
            likely_root_cause=likely_root_cause,
            localized_code_region=region,
            evidence_summary=evidence,
            recommended_repair_direction=recommended,
            confidence_score=confidence,
            confidence_band=self._confidence_band(confidence),
            uncertainty_notes=uncertainty,
            alternative_hypotheses=alternatives,
            direct_cause=result.exception_message,
            downstream_symptom="Execution stopped when Python evaluated the undefined name.",
            repair_hints=repair_hints,
        )

    def _diagnose_import_error(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result
        region = self._localized_region(request.code, result.failure_line)
        evidence = self._base_evidence(result, region)
        missing_module = self._extract_missing_module(result)
        if missing_module:
            evidence.append(f"Missing module from execution result: {missing_module}")

        confidence = 0.87
        likely_root_cause = "The script imports a module that is not available in the current single-file execution environment."
        recommended = "Fix or remove the failing import, or replace it with logic that does not assume hidden project files or unavailable packages."
        uncertainty = "The import failure is direct, but the intended replacement depends on whether the module was supposed to be standard-library, local, or optional."
        alternatives = [
            AlternativeHypothesis(
                bug_class="missing_file_or_resource",
                reason="If the import targeted a local helper file, the dependency is outside the current single-file scope.",
                confidence_band="medium",
            )
        ]

        return DiagnoserResult(
            primary_bug_class="import_error",
            likely_root_cause=likely_root_cause,
            localized_code_region=region,
            evidence_summary=evidence,
            recommended_repair_direction=recommended,
            confidence_score=confidence,
            confidence_band=self._confidence_band(confidence),
            uncertainty_notes=uncertainty,
            alternative_hypotheses=alternatives,
            direct_cause=result.exception_message,
            downstream_symptom="Execution stopped while resolving imports before the main logic could continue.",
            repair_hints={"missing_module": missing_module, "line_number": result.failure_line},
        )

    def _diagnose_missing_resource(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result
        region = self._localized_region(request.code, result.failure_line)
        evidence = self._base_evidence(result, region)
        missing_path = self._extract_missing_path(result)
        if missing_path:
            evidence.append(f"Missing file or resource from execution result: {missing_path}")

        confidence = 0.88
        likely_root_cause = "The code tries to read a missing resource or file that is not present in the current execution directory."
        recommended = "Update the path, provide the expected file explicitly, or guard the read so the code handles missing resources conservatively."
        uncertainty = "The missing resource is directly observed, but the intended file location may still depend on user context that is not present in this single-file prototype."
        alternatives = [
            AlternativeHypothesis(
                bug_class="runtime_exception",
                reason="If the path is generated dynamically, the upstream bug may be incorrect path construction rather than a truly absent file.",
                confidence_band="medium",
            )
        ]

        return DiagnoserResult(
            primary_bug_class="file_path_or_missing_resource",
            likely_root_cause=likely_root_cause,
            localized_code_region=region,
            evidence_summary=evidence,
            recommended_repair_direction=recommended,
            confidence_score=confidence,
            confidence_band=self._confidence_band(confidence),
            uncertainty_notes=uncertainty,
            alternative_hypotheses=alternatives,
            direct_cause=result.exception_message,
            downstream_symptom="Execution failed at the file access point.",
            repair_hints={"missing_path": missing_path, "line_number": result.failure_line},
        )

    def _diagnose_type_error(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result
        region = self._localized_region(request.code, result.failure_line)
        evidence = self._base_evidence(result, region)
        message = result.exception_message or ""
        confidence = 0.7
        likely_root_cause = "A value is being used with an incompatible type at the localized statement."
        recommended = "Inspect the values and call signature at the localized line and align the argument types or count before patching more broadly."
        uncertainty = "TypeError evidence points to the failing operation, but the direct cause may be upstream data flow rather than the localized expression alone."
        alternatives: list[AlternativeHypothesis] = []
        repair_hints: dict[str, object] = {"line_number": result.failure_line}

        if "positional argument" in message or "required positional argument" in message:
            confidence = 0.86
            likely_root_cause = "A function or callable is being invoked with the wrong number of arguments."
            recommended = "Match the call site to the function signature, or adjust the definition if the call is the intended behavior."
            repair_hints["remove_call_arguments"] = True
            alternatives.append(
                AlternativeHypothesis(
                    bug_class="runtime_exception",
                    reason="If the callable is reassigned earlier, the mismatch may come from using the wrong object as a function.",
                    confidence_band="low",
                )
            )
            primary_bug_class = "argument_mismatch"
        elif "unsupported operand type" in message:
            confidence = 0.45
            likely_root_cause = "An operation uses incompatible operand types, but the underlying source value may be wrong earlier in the program."
            recommended = "Trace the values feeding the localized expression and normalize types instead of assuming a one-line fix."
            uncertainty = "The failing line is known, but the root cause may be upstream value construction or missing type conversion."
            alternatives = [
                AlternativeHypothesis(
                    bug_class="simple_logic_mismatch",
                    reason="If the values are correct individually, the wrong operator or formatting approach may have been chosen.",
                    confidence_band="medium",
                ),
                AlternativeHypothesis(
                    bug_class="runtime_exception",
                    reason="The direct problem may be an unexpected input shape that was never validated before this line.",
                    confidence_band="medium",
                ),
            ]
            primary_bug_class = "common_runtime_exception"
        else:
            alternatives.append(
                AlternativeHypothesis(
                    bug_class="common_runtime_exception",
                    reason="The localized operation may be correct, and the actual mistake may be the upstream value passed into it.",
                    confidence_band="medium",
                )
            )
            primary_bug_class = "common_runtime_exception"

        return DiagnoserResult(
            primary_bug_class=primary_bug_class,
            likely_root_cause=likely_root_cause,
            localized_code_region=region,
            evidence_summary=evidence,
            recommended_repair_direction=recommended,
            confidence_score=confidence,
            confidence_band=self._confidence_band(confidence),
            uncertainty_notes=uncertainty,
            alternative_hypotheses=alternatives,
            direct_cause=result.exception_message,
            downstream_symptom="Execution failed when Python evaluated the localized runtime operation.",
            repair_hints=repair_hints,
        )

    def _diagnose_output_mismatch(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result
        region = self._localized_region(request.code, None)
        evidence = [
            "The script executed successfully, so no runtime exception directly localized the problem.",
            f"Observed stdout: {result.stdout.strip()}",
            f"Expected output: {request.expected_output}",
        ]
        return DiagnoserResult(
            primary_bug_class="simple_logic_mismatch",
            likely_root_cause="Observed output differs from the expected output, but execution evidence does not localize the bug to one line.",
            localized_code_region=region,
            evidence_summary=evidence,
            recommended_repair_direction="Compare the code path producing stdout with the expected behavior before editing unrelated sections.",
            confidence_score=0.34,
            confidence_band=self._confidence_band(0.34),
            uncertainty_notes="No exception was raised, so localization is weak and the mismatch may require human inspection of program intent.",
            alternative_hypotheses=[
                AlternativeHypothesis(
                    bug_class="common_runtime_exception",
                    reason="The logic may be correct, and the expectation itself may be stale or incomplete.",
                    confidence_band="low",
                )
            ],
            direct_cause="Output mismatch",
            downstream_symptom="The script completes but does not match the expected observable behavior.",
        )

    def _diagnose_generic_runtime_exception(self, request: DiagnoserRequest) -> DiagnoserResult:
        result = request.latest_execution_result
        region = self._localized_region(request.code, result.failure_line)
        evidence = self._base_evidence(result, region)
        confidence = 0.38
        likely_root_cause = "Execution evidence shows a runtime failure, but it does not support a narrow repair hypothesis yet."
        recommended = "Inspect the localized statement and the values reaching it before attempting a patch."
        uncertainty = "The exception identifies where execution failed, but not enough evidence is available to separate direct cause from upstream symptom confidently."
        alternatives = [
            AlternativeHypothesis(
                bug_class="common_runtime_exception",
                reason="The localized line may be correct and only expose an earlier bad value or state.",
                confidence_band="medium",
            )
        ]

        return DiagnoserResult(
            primary_bug_class="common_runtime_exception",
            likely_root_cause=likely_root_cause,
            localized_code_region=region,
            evidence_summary=evidence,
            recommended_repair_direction=recommended,
            confidence_score=confidence,
            confidence_band=self._confidence_band(confidence),
            uncertainty_notes=uncertainty,
            alternative_hypotheses=alternatives,
            direct_cause=result.exception_message,
            downstream_symptom="Execution terminated with an exception before completing the intended flow.",
            repair_hints={"line_number": result.failure_line},
        )

    def _localized_region(self, code: str, line_number: int | None) -> CodeRegion:
        lines = code.splitlines()
        if not lines:
            return CodeRegion()
        if line_number is None or line_number < 1 or line_number > len(lines):
            snippet = "\n".join(lines[: min(3, len(lines))])
            return CodeRegion(
                start_line=1,
                end_line=min(3, len(lines)),
                snippet=snippet,
            )
        return CodeRegion(
            start_line=line_number,
            end_line=line_number,
            snippet=lines[line_number - 1],
        )

    def _base_evidence(self, result: ExecutionResult, region: CodeRegion) -> list[str]:
        evidence = [
            f"Outcome label from executor: {result.outcome_label}",
            f"Exception type from executor: {result.exception_type or 'none'}",
            f"Exception message from executor: {result.exception_message or ''}",
        ]
        if region.start_line is not None:
            evidence.append(
                f"Localized code region: line {region.start_line}"
                + (f"-{region.end_line}" if region.end_line and region.end_line != region.start_line else "")
                + f" -> {region.snippet}"
            )
        return evidence

    @staticmethod
    def _extract_name_error_symbol(result: ExecutionResult) -> str | None:
        if not result.exception_message:
            return None
        match = re.search(r"name '([A-Za-z_][A-Za-z0-9_]*)' is not defined", result.exception_message)
        return match.group(1) if match else None

    @staticmethod
    def _extract_missing_module(result: ExecutionResult) -> str | None:
        if not result.exception_message:
            return None
        match = re.search(r"No module named '([^']+)'", result.exception_message)
        return match.group(1) if match else None

    @staticmethod
    def _extract_missing_path(result: ExecutionResult) -> str | None:
        if not result.exception_message:
            return None
        match = re.search(r"No such file or directory: '([^']+)'", result.exception_message)
        return match.group(1) if match else None

    def _closest_known_identifier(self, code: str, missing_name: str | None) -> str | None:
        if not missing_name:
            return None
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None

        collector = _IdentifierCollector(names=set())
        collector.visit(tree)
        candidates = sorted(name for name in collector.names if name != missing_name)
        closest = difflib.get_close_matches(missing_name, candidates, n=1, cutoff=0.75)
        return closest[0] if closest else None

    @staticmethod
    def _confidence_band(confidence_score: float) -> str:
        if confidence_score >= 0.8:
            return "high"
        if confidence_score >= 0.55:
            return "medium"
        return "low"

    @staticmethod
    def _merge_uncertainty_with_history(
        existing_notes: str,
        prior_patch_history: list[str],
        prior_verifier_feedback: list[str],
    ) -> str:
        fragments = [existing_notes]
        if prior_patch_history:
            fragments.append(
                "Prior patch history exists, so the next diagnosis should avoid repeating the same failed repair direction without new evidence."
            )
        if prior_verifier_feedback:
            fragments.append(
                "Verifier feedback indicates earlier repair attempts did not fully resolve the issue, which lowers confidence in one-line explanations."
            )
        return " ".join(fragment for fragment in fragments if fragment).strip()
