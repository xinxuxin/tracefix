from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from tracefix.state import SessionState
from tracefix.types import to_dict


class TraceLogger:
    """Writes reviewer-friendly traces and saved patch artifacts."""

    def __init__(self, trace_dir: str | Path, patch_dir: str | Path) -> None:
        self.trace_dir = Path(trace_dir)
        self.patch_dir = Path(patch_dir)

    def create_session_dir(
        self,
        *,
        base_dir: str | Path,
        file_stem: str,
        session_id: str,
    ) -> Path:
        session_dir = Path(base_dir) / f"{file_stem}_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def append_event(self, trace_path: str | Path, event: dict[str, Any]) -> None:
        path = Path(trace_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            **event,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(to_dict(payload), ensure_ascii=True) + "\n")

    def write_trace(self, state: SessionState, file_stem: str) -> Path:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        trace_path = self.trace_dir / f"{file_stem}_{state.session_id}.json"
        state.trace_path = str(trace_path)
        trace_path.write_text(json.dumps(to_dict(state), indent=2), encoding="utf-8")
        return trace_path

    def write_state_snapshot(self, state: SessionState, destination: str | Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        state.trace_path = str(path)
        path.write_text(json.dumps(to_dict(state), indent=2), encoding="utf-8")
        return path

    def write_patch(self, file_stem: str, session_id: str, patched_source: str) -> Path:
        self.patch_dir.mkdir(parents=True, exist_ok=True)
        patch_path = self.patch_dir / f"{file_stem}_{session_id}.py"
        patch_path.write_text(patched_source, encoding="utf-8")
        return patch_path

    def write_text(self, destination: str | Path, content: str) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
