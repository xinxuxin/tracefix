from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from typing import Protocol


class ProviderError(RuntimeError):
    """Raised when a provider request or response cannot be used safely."""


@dataclass(frozen=True)
class ProviderGeneration:
    """Structured provider response after JSON extraction."""

    provider_name: str
    model_name: str
    payload: dict[str, Any]
    raw_text: str


class LLMProvider(Protocol):
    """Minimal provider contract for JSON-only component prompting."""

    provider_name: str
    model_name: str

    def generate_json(
        self,
        prompt: str,
        *,
        temperature: float,
        timeout_seconds: int,
        max_tokens: int,
    ) -> ProviderGeneration:
        ...


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Extract the first JSON object from model text."""

    text = raw_text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    candidate = _find_first_braced_object(text)
    if candidate is None:
        raise ProviderError("Provider output did not contain a valid JSON object.")

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ProviderError("Provider output JSON could not be parsed.") from exc

    if not isinstance(payload, dict):
        raise ProviderError("Provider output JSON must be an object.")
    return payload


def _find_first_braced_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None
