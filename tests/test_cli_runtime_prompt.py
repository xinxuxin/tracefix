from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tracefix.cli import _prompt_for_provider_api_key_if_needed
from tracefix.config import TraceFixConfig


class CliRuntimePromptTests(unittest.TestCase):
    def test_prompt_sets_openai_key_for_current_session_only(self) -> None:
        config = TraceFixConfig(
            provider_mode="openai",
            enable_llm_diagnoser=True,
        )
        with patch.dict(os.environ, {}, clear=True):
            prompted = _prompt_for_provider_api_key_if_needed(
                config,
                prompt_fn=lambda _: "sk-test-123",
                stdin_isatty=True,
            )

            self.assertTrue(prompted)
            self.assertEqual(os.environ.get("OPENAI_API_KEY"), "sk-test-123")

    def test_prompt_is_skipped_when_input_is_blank(self) -> None:
        config = TraceFixConfig(
            provider_mode="anthropic",
            enable_llm_patcher=True,
        )
        with patch.dict(os.environ, {}, clear=True):
            prompted = _prompt_for_provider_api_key_if_needed(
                config,
                prompt_fn=lambda _: "   ",
                stdin_isatty=True,
            )

            self.assertFalse(prompted)
            self.assertIsNone(os.environ.get("ANTHROPIC_API_KEY"))

    def test_prompt_is_skipped_in_non_interactive_mode(self) -> None:
        config = TraceFixConfig(
            provider_mode="openai",
            enable_llm_diagnoser=True,
        )
        with patch.dict(os.environ, {}, clear=True):
            prompted = _prompt_for_provider_api_key_if_needed(
                config,
                prompt_fn=lambda _: "sk-should-not-be-used",
                stdin_isatty=False,
            )

            self.assertFalse(prompted)
            self.assertIsNone(os.environ.get("OPENAI_API_KEY"))


if __name__ == "__main__":
    unittest.main()
