from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.agents.diagnoser_agent import DiagnoserAgent
from tracefix.agents.patcher_agent import PatcherAgent
from tracefix.config import TraceFixConfig
from tracefix.orchestrator.controller import TraceFixController
from tracefix.providers.base import ProviderError
from tracefix.providers.base import ProviderGeneration
from tracefix.providers.factory import resolve_provider
from tracefix.types import CodeRegion
from tracefix.types import DiagnoserRequest
from tracefix.types import DiagnoserResult
from tracefix.types import ExecutionResult
from tracefix.types import PatcherRequest


class _StubProvider:
    def __init__(self, provider_name: str, model_name: str, payload: dict[str, object]) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.payload = payload

    def generate_json(
        self,
        prompt: str,
        *,
        temperature: float,
        timeout_seconds: int,
        max_tokens: int,
    ) -> ProviderGeneration:
        return ProviderGeneration(
            provider_name=self.provider_name,
            model_name=self.model_name,
            payload=self.payload,
            raw_text=json.dumps(self.payload),
        )


class _FailingProvider:
    provider_name = "openai"
    model_name = "gpt-4.1"

    def generate_json(
        self,
        prompt: str,
        *,
        temperature: float,
        timeout_seconds: int,
        max_tokens: int,
    ) -> ProviderGeneration:
        raise ProviderError("simulated provider failure")


class ProviderModeTests(unittest.TestCase):
    def test_provider_selection_falls_back_when_key_missing(self) -> None:
        config = TraceFixConfig(
            provider_mode="openai",
            enable_llm_diagnoser=True,
        )
        with patch.dict(os.environ, {}, clear=True):
            resolution = resolve_provider(config, component_name="diagnoser")

        self.assertIsNone(resolution.provider)
        self.assertEqual(resolution.provider_name, "openai")
        self.assertIn("OPENAI_API_KEY", resolution.error or "")

    def test_diagnoser_can_use_injected_provider(self) -> None:
        config = TraceFixConfig(
            provider_mode="openai",
            enable_llm_diagnoser=True,
        )
        provider = _StubProvider(
            "openai",
            "gpt-4.1",
            {
                "primary_bug_class": "name_error",
                "likely_root_cause": "The undefined name is a typo for an existing variable.",
                "localized_code_region": {"start_line": 3, "end_line": 3, "snippet": "print(message)"},
                "evidence_summary": ["NameError identifies message as undefined."],
                "recommended_repair_direction": "Replace message with messgae on the localized line.",
                "confidence_score": 0.92,
                "confidence_band": "high",
                "uncertainty_notes": "Low uncertainty because there is one obvious nearby identifier.",
                "alternative_hypotheses": [],
                "repair_hints": {"target_name": "message", "replacement_name": "messgae", "line_number": 3},
            },
        )
        agent = DiagnoserAgent(config=config, provider=provider)
        result = ExecutionResult(
            command=["python3.11", "target.py"],
            return_code=1,
            stdout="",
            stderr="NameError: name 'message' is not defined",
            timed_out=False,
            duration_ms=12,
            exception_type="NameError",
            exception_message="name 'message' is not defined",
            failure_line=3,
            outcome_label="runtime_exception",
        )

        diagnosis = agent.diagnose(DiagnoserRequest(code='messgae = "hi"\nprint(message)\n', latest_execution_result=result))

        self.assertEqual(diagnosis.execution_mode, "openai")
        self.assertEqual(diagnosis.provider_name, "openai")
        self.assertEqual(diagnosis.model_name, "gpt-4.1")
        self.assertEqual(diagnosis.repair_hints["replacement_name"], "messgae")

    def test_patcher_falls_back_to_local_when_provider_fails(self) -> None:
        config = TraceFixConfig(
            provider_mode="openai",
            enable_llm_patcher=True,
            fallback_to_local_on_provider_error=True,
        )
        agent = PatcherAgent(config=config, provider=_FailingProvider())
        diagnosis = DiagnoserResult(
            primary_bug_class="syntax_error",
            likely_root_cause="A block-opening statement is likely missing a trailing colon.",
            localized_code_region=CodeRegion(start_line=1, end_line=1, snippet="def countdown(start)"),
            evidence_summary=["Line 1 is missing a colon."],
            recommended_repair_direction="Add the missing colon.",
            confidence_score=0.96,
            confidence_band="high",
            uncertainty_notes="",
            repair_hints={"missing_colon": True, "line_number": 1},
        )

        patch_result = agent.patch(PatcherRequest(code="def countdown(start)\n    return start\n", diagnosis_result=diagnosis))

        self.assertEqual(patch_result.execution_mode, "local")
        self.assertTrue(patch_result.fallback_used)
        self.assertIn("provider failure", patch_result.provider_error or "")
        self.assertIn("def countdown(start):", patch_result.updated_code)

    def test_controller_trace_records_provider_metadata_on_fallback(self) -> None:
        config = TraceFixConfig(
            max_attempts=1,
            timeout_seconds=1,
            provider_mode="openai",
            enable_llm_diagnoser=True,
            enable_llm_patcher=True,
            fallback_to_local_on_provider_error=True,
        )
        with tempfile.TemporaryDirectory(prefix="tracefix_provider_trace_") as temp_dir:
            base = Path(temp_dir)
            script_path = base / "name_error_bug.py"
            script_path.write_text(
                (
                    'def greet(name):\n'
                    '    messgae = f"Hello, {name}!"\n'
                    "    print(message)\n\n"
                    'greet("TraceFix")\n'
                ),
                encoding="utf-8",
            )

            controller = TraceFixController(
                config=config,
                trace_dir=base / "traces",
                patch_dir=base / "patches",
                session_root=base / "sessions",
            )
            controller.diagnoser = DiagnoserAgent(config=config, provider=_FailingProvider())
            controller.patcher = PatcherAgent(config=config, provider=_FailingProvider())

            state = controller.debug_file(script_path, expected_output="Hello, TraceFix!\n", max_retries=1)
            trace_text = Path(state.trace_events_path).read_text(encoding="utf-8")

        self.assertIn('"handoff": "diagnoser -> controller"', trace_text)
        self.assertIn('"handoff": "patcher -> controller"', trace_text)
        self.assertIn('"fallback_used": true', trace_text)
        self.assertIn('"provider_name": "openai"', trace_text)


if __name__ == "__main__":
    unittest.main()
