from __future__ import annotations

from typing import Any

from tracefix.providers.base import ProviderError
from tracefix.providers.base import ProviderGeneration
from tracefix.providers.base import extract_json_object


class OpenAIProvider:
    """Thin wrapper around the official OpenAI Python SDK."""

    provider_name = "openai"

    def __init__(self, *, api_key: str, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name

    def generate_json(
        self,
        prompt: str,
        *,
        timeout_seconds: int,
        max_tokens: int,
    ) -> ProviderGeneration:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("OpenAI SDK is not installed. Install it with `pip install openai`.") from exc

        client = OpenAI(api_key=self.api_key, timeout=timeout_seconds)
        try:
            response = client.responses.create(
                model=self.model_name,
                input=prompt,
                max_output_tokens=max_tokens,
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI provider request failed: {exc}") from exc

        raw_text = _extract_openai_text(response)
        payload = extract_json_object(raw_text)
        return ProviderGeneration(
            provider_name=self.provider_name,
            model_name=self.model_name,
            payload=payload,
            raw_text=raw_text,
        )


def _extract_openai_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = getattr(response, "output", None)
    if isinstance(output, list):
        fragments: list[str] = []
        for item in output:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if isinstance(text, str):
                    fragments.append(text)
        if fragments:
            return "\n".join(fragments)

    raise ProviderError("OpenAI provider returned no usable text output.")
