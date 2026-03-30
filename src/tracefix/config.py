from __future__ import annotations

import json
import os
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path


def _read_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


@dataclass(frozen=True)
class TraceFixConfig:
    """Minimal runtime configuration for the local CLI workflow."""

    max_attempts: int = 2
    timeout_seconds: int = 2
    trace_dir: Path = Path("logs/traces")
    patch_dir: Path = Path("outputs/patches")
    log_dir: Path = Path("logs")
    evaluation_dir: Path = Path("evaluation")
    provider_mode: str = "local"
    provider_model_name: str | None = None
    openai_model_name: str = "gpt-4.1"
    anthropic_model_name: str = "claude-3-5-sonnet-latest"
    api_timeout_seconds: int = 20
    api_max_tokens: int = 1200
    enable_llm_diagnoser: bool = False
    enable_llm_patcher: bool = False
    enable_llm_verifier_assist: bool = False
    fallback_to_local_on_provider_error: bool = True

    @classmethod
    def from_json(cls, config_path: str | Path) -> "TraceFixConfig":
        payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
        return cls(
            max_attempts=int(payload.get("max_attempts", 2)),
            timeout_seconds=int(payload.get("timeout_seconds", 2)),
            trace_dir=Path(payload.get("trace_dir", "logs/traces")),
            patch_dir=Path(payload.get("patch_dir", "outputs/patches")),
            log_dir=Path(payload.get("log_dir", "logs")),
            evaluation_dir=Path(payload.get("evaluation_dir", "evaluation")),
            provider_mode=str(payload.get("provider_mode", "local")).lower(),
            provider_model_name=payload.get("provider_model_name"),
            openai_model_name=str(payload.get("openai_model_name", "gpt-4.1")),
            anthropic_model_name=str(payload.get("anthropic_model_name", "claude-3-5-sonnet-latest")),
            api_timeout_seconds=int(payload.get("api_timeout_seconds", 20)),
            api_max_tokens=int(payload.get("api_max_tokens", 1200)),
            enable_llm_diagnoser=_read_bool(payload.get("enable_llm_diagnoser"), False),
            enable_llm_patcher=_read_bool(payload.get("enable_llm_patcher"), False),
            enable_llm_verifier_assist=_read_bool(payload.get("enable_llm_verifier_assist"), False),
            fallback_to_local_on_provider_error=_read_bool(
                payload.get("fallback_to_local_on_provider_error"),
                True,
            ),
        )

    @classmethod
    def from_env(cls) -> "TraceFixConfig":
        return cls(
            max_attempts=int(os.getenv("TRACEFIX_MAX_ATTEMPTS", "2")),
            timeout_seconds=int(os.getenv("TRACEFIX_TIMEOUT_SECONDS", "2")),
            trace_dir=Path(os.getenv("TRACEFIX_TRACE_DIR", "logs/traces")),
            patch_dir=Path(os.getenv("TRACEFIX_PATCH_DIR", "outputs/patches")),
            log_dir=Path(os.getenv("TRACEFIX_LOG_DIR", "logs")),
            evaluation_dir=Path(os.getenv("TRACEFIX_EVALUATION_DIR", "evaluation")),
            provider_mode=os.getenv("TRACEFIX_PROVIDER_MODE", "local").lower(),
            provider_model_name=os.getenv("TRACEFIX_PROVIDER_MODEL"),
            openai_model_name=os.getenv("TRACEFIX_OPENAI_MODEL", "gpt-4.1"),
            anthropic_model_name=os.getenv(
                "TRACEFIX_ANTHROPIC_MODEL",
                "claude-3-5-sonnet-latest",
            ),
            api_timeout_seconds=int(os.getenv("TRACEFIX_API_TIMEOUT_SECONDS", "20")),
            api_max_tokens=int(os.getenv("TRACEFIX_API_MAX_TOKENS", "1200")),
            enable_llm_diagnoser=_read_bool(os.getenv("TRACEFIX_ENABLE_LLM_DIAGNOSER"), False),
            enable_llm_patcher=_read_bool(os.getenv("TRACEFIX_ENABLE_LLM_PATCHER"), False),
            enable_llm_verifier_assist=_read_bool(os.getenv("TRACEFIX_ENABLE_LLM_VERIFIER_ASSIST"), False),
            fallback_to_local_on_provider_error=_read_bool(
                os.getenv("TRACEFIX_FALLBACK_TO_LOCAL_ON_PROVIDER_ERROR"),
                True,
            ),
        )

    def merge(self, other: "TraceFixConfig") -> "TraceFixConfig":
        return replace(
            self,
            max_attempts=other.max_attempts,
            timeout_seconds=other.timeout_seconds,
            trace_dir=other.trace_dir,
            patch_dir=other.patch_dir,
            log_dir=other.log_dir,
            evaluation_dir=other.evaluation_dir,
            provider_mode=other.provider_mode,
            provider_model_name=other.provider_model_name,
            openai_model_name=other.openai_model_name,
            anthropic_model_name=other.anthropic_model_name,
            api_timeout_seconds=other.api_timeout_seconds,
            api_max_tokens=other.api_max_tokens,
            enable_llm_diagnoser=other.enable_llm_diagnoser,
            enable_llm_patcher=other.enable_llm_patcher,
            enable_llm_verifier_assist=other.enable_llm_verifier_assist,
            fallback_to_local_on_provider_error=other.fallback_to_local_on_provider_error,
        )

    def with_overrides(
        self,
        *,
        max_attempts: int | None = None,
        timeout_seconds: int | None = None,
        trace_dir: str | Path | None = None,
        patch_dir: str | Path | None = None,
        provider_mode: str | None = None,
        provider_model_name: str | None = None,
        api_timeout_seconds: int | None = None,
        api_max_tokens: int | None = None,
        enable_llm_diagnoser: bool | None = None,
        enable_llm_patcher: bool | None = None,
        enable_llm_verifier_assist: bool | None = None,
        fallback_to_local_on_provider_error: bool | None = None,
    ) -> "TraceFixConfig":
        return replace(
            self,
            max_attempts=max_attempts if max_attempts is not None else self.max_attempts,
            timeout_seconds=timeout_seconds if timeout_seconds is not None else self.timeout_seconds,
            trace_dir=Path(trace_dir) if trace_dir is not None else self.trace_dir,
            patch_dir=Path(patch_dir) if patch_dir is not None else self.patch_dir,
            provider_mode=provider_mode if provider_mode is not None else self.provider_mode,
            provider_model_name=provider_model_name if provider_model_name is not None else self.provider_model_name,
            api_timeout_seconds=api_timeout_seconds if api_timeout_seconds is not None else self.api_timeout_seconds,
            api_max_tokens=api_max_tokens if api_max_tokens is not None else self.api_max_tokens,
            enable_llm_diagnoser=(
                enable_llm_diagnoser if enable_llm_diagnoser is not None else self.enable_llm_diagnoser
            ),
            enable_llm_patcher=enable_llm_patcher if enable_llm_patcher is not None else self.enable_llm_patcher,
            enable_llm_verifier_assist=(
                enable_llm_verifier_assist
                if enable_llm_verifier_assist is not None
                else self.enable_llm_verifier_assist
            ),
            fallback_to_local_on_provider_error=(
                fallback_to_local_on_provider_error
                if fallback_to_local_on_provider_error is not None
                else self.fallback_to_local_on_provider_error
            ),
        )

    def ensure_directories(self) -> None:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.patch_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)
