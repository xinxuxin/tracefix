from __future__ import annotations

import os
from dataclasses import dataclass

from tracefix.config import TraceFixConfig
from tracefix.providers.anthropic_provider import AnthropicProvider
from tracefix.providers.base import LLMProvider
from tracefix.providers.openai_provider import OpenAIProvider


@dataclass(frozen=True)
class ProviderResolution:
    provider: LLMProvider | None
    provider_name: str | None
    model_name: str | None
    error: str | None = None


def resolve_provider(config: TraceFixConfig, *, component_name: str) -> ProviderResolution:
    if not _component_enabled(config, component_name):
        return ProviderResolution(provider=None, provider_name=None, model_name=None, error=None)

    mode = (config.provider_mode or "local").lower()
    if mode == "local":
        return ProviderResolution(provider=None, provider_name=None, model_name=None, error=None)

    model_name = _resolve_model_name(config, mode)
    if mode == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ProviderResolution(
                provider=None,
                provider_name="openai",
                model_name=model_name,
                error="OPENAI_API_KEY is not set; falling back to local mode.",
            )
        return ProviderResolution(
            provider=OpenAIProvider(api_key=api_key, model_name=model_name),
            provider_name="openai",
            model_name=model_name,
            error=None,
        )

    if mode == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return ProviderResolution(
                provider=None,
                provider_name="anthropic",
                model_name=model_name,
                error="ANTHROPIC_API_KEY is not set; falling back to local mode.",
            )
        return ProviderResolution(
            provider=AnthropicProvider(api_key=api_key, model_name=model_name),
            provider_name="anthropic",
            model_name=model_name,
            error=None,
        )

    return ProviderResolution(
        provider=None,
        provider_name=mode,
        model_name=model_name,
        error=f"Unsupported provider mode '{mode}'; falling back to local mode.",
    )


def _component_enabled(config: TraceFixConfig, component_name: str) -> bool:
    if component_name == "diagnoser":
        return config.enable_llm_diagnoser
    if component_name == "patcher":
        return config.enable_llm_patcher
    if component_name == "verifier":
        return config.enable_llm_verifier_assist
    return False


def _resolve_model_name(config: TraceFixConfig, mode: str) -> str | None:
    if config.provider_model_name:
        return config.provider_model_name
    if mode == "openai":
        return config.openai_model_name
    if mode == "anthropic":
        return config.anthropic_model_name
    return None
