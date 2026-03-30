from __future__ import annotations

from tracefix.providers.base import ProviderError
from tracefix.providers.base import ProviderGeneration
from tracefix.providers.base import extract_json_object


class AnthropicProvider:
    """Thin wrapper around the Anthropic Python SDK."""

    provider_name = "anthropic"

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
            from anthropic import Anthropic
        except ImportError as exc:
            raise ProviderError(
                "Anthropic SDK is not installed. Install it with `pip install anthropic`."
            ) from exc

        client = Anthropic(api_key=self.api_key, timeout=timeout_seconds)
        try:
            response = client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderError(f"Anthropic provider request failed: {exc}") from exc

        parts: list[str] = []
        for block in getattr(response, "content", []) or []:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        raw_text = "\n".join(parts).strip()
        if not raw_text:
            raise ProviderError("Anthropic provider returned no usable text output.")

        payload = extract_json_object(raw_text)
        return ProviderGeneration(
            provider_name=self.provider_name,
            model_name=self.model_name,
            payload=payload,
            raw_text=raw_text,
        )
