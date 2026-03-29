from __future__ import annotations

import json
import os
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path


@dataclass(frozen=True)
class TraceFixConfig:
    """Minimal runtime configuration for the local CLI workflow."""

    max_attempts: int = 2
    timeout_seconds: int = 2
    trace_dir: Path = Path("logs/traces")
    patch_dir: Path = Path("outputs/patches")
    log_dir: Path = Path("logs")
    evaluation_dir: Path = Path("evaluation")

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
        )

    def with_overrides(
        self,
        *,
        max_attempts: int | None = None,
        timeout_seconds: int | None = None,
        trace_dir: str | Path | None = None,
        patch_dir: str | Path | None = None,
    ) -> "TraceFixConfig":
        return replace(
            self,
            max_attempts=max_attempts if max_attempts is not None else self.max_attempts,
            timeout_seconds=timeout_seconds if timeout_seconds is not None else self.timeout_seconds,
            trace_dir=Path(trace_dir) if trace_dir is not None else self.trace_dir,
            patch_dir=Path(patch_dir) if patch_dir is not None else self.patch_dir,
        )

    def ensure_directories(self) -> None:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.patch_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)

