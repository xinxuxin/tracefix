# Model and Provider Policy

TraceFix is local-first. External model providers are optional enhancements for diagnosis and patch synthesis only; they are not required to run the CLI, tests, frontend, or evaluation package.

## Default Mode

| Setting | Default |
|---|---:|
| Provider mode | `local` |
| LLM Diagnoser enabled | `false` |
| LLM Patcher enabled | `false` |
| LLM Verifier assist enabled | `false` |
| Fallback on provider error | `true` |

Defaults are defined in [src/tracefix/config.py](/Users/macbook/Desktop/agentic/src/tracefix/config.py) and mirrored in [config/settings.example.json](/Users/macbook/Desktop/agentic/config/settings.example.json).

## Component Assignments

| Component | Default execution | Optional provider use | Notes |
|---|---|---|---|
| Controller | deterministic local | none | Owns state, retries, final status, and artifact persistence. |
| Executor | deterministic local | none | Runs bounded Python subprocess execution and records evidence. |
| Diagnoser | local rules | OpenAI or Anthropic when enabled | Provider output must be JSON and is coerced back into `DiagnoserResult`. |
| Patcher | local rules/templates | OpenAI or Anthropic when enabled | Provider patch must pass local safeguards before use. |
| Verifier | deterministic local | config flag exists for future assist, but current verifier remains rules-first | Verifier decides accept/retry/escalate/stop and must not accept merely because a script no longer crashes. |
| Frontend / Visual API | deterministic local | none | Reads local session and evaluation artifacts. |

## Provider Options

| Provider mode | Environment variable | Default model | Temperature | Max tokens | Timeout |
|---|---|---:|---:|---:|---:|
| `openai` | `OPENAI_API_KEY` | `gpt-4.1` | `0.0` | `1200` | `20s` |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-latest` | `0.0` | `1200` | `20s` |

Model and runtime settings may be overridden through:

- `TRACEFIX_PROVIDER_MODE`
- `TRACEFIX_PROVIDER_MODEL`
- `TRACEFIX_OPENAI_MODEL`
- `TRACEFIX_ANTHROPIC_MODEL`
- `TRACEFIX_API_TEMPERATURE`
- `TRACEFIX_API_MAX_TOKENS`
- `TRACEFIX_API_TIMEOUT_SECONDS`
- `TRACEFIX_ENABLE_LLM_DIAGNOSER`
- `TRACEFIX_ENABLE_LLM_PATCHER`
- `TRACEFIX_ENABLE_LLM_VERIFIER_ASSIST`

## Secret Handling

API keys must be provided through environment variables or the CLI's hidden runtime prompt. They are not stored in JSON config files, session artifacts, traces, or committed repository files.

If provider mode is enabled and the matching key is missing:

- interactive CLI use prompts once for the key and keeps it in the current process only
- non-interactive runs fall back to local behavior when fallback is enabled
- trace metadata records provider name, model name, fallback status, and provider error, but not the key

## Fallback Behavior

TraceFix falls back to local logic when:

- provider mode is `local`
- the component-specific LLM flag is disabled
- the API key is missing
- the provider SDK is not installed
- the provider request fails
- the provider returns invalid or unsafe JSON
- patch safeguards reject a provider-proposed patch

Fallback behavior is recorded in:

- `trace.jsonl` handoff events
- `session_state.json`
- `summary.md` and `failure_summary.md` where applicable

## Prompt and Output Policy

Provider prompts live in:

- [src/tracefix/prompts/diagnoser_prompt.txt](/Users/macbook/Desktop/agentic/src/tracefix/prompts/diagnoser_prompt.txt)
- [src/tracefix/prompts/patcher_prompt.txt](/Users/macbook/Desktop/agentic/src/tracefix/prompts/patcher_prompt.txt)

Provider outputs must be JSON objects. TraceFix extracts and coerces provider JSON into typed local dataclasses before continuing. The provider does not receive authority to change retry policy, verification acceptance, sandbox scope, or final session status.

## Phase 3 Evaluation Note

The Phase 3 evaluation artifacts checked into this repository were produced in local deterministic mode. This makes the evidence reproducible without external services while still documenting the optional provider architecture.
