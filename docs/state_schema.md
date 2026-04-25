# State Schema and Write Permissions

TraceFix uses stateless worker components and a stateful controller. The Executor, Diagnoser, Patcher, and Verifier each return typed results; the Controller owns the session lifecycle, retry count, persistence, and final decision.

Primary implementation files:

- [src/tracefix/state.py](/Users/macbook/Desktop/agentic/src/tracefix/state.py)
- [src/tracefix/types.py](/Users/macbook/Desktop/agentic/src/tracefix/types.py)
- [src/tracefix/models.py](/Users/macbook/Desktop/agentic/src/tracefix/models.py)
- [src/tracefix/orchestrator/controller.py](/Users/macbook/Desktop/agentic/src/tracefix/orchestrator/controller.py)

## Session State Fields

| State object / field | Type | Written by | Read by | Purpose | Persistence location |
|---|---|---|---|---|---|
| `SessionState.session_id` | `str` | Controller | All artifact readers | Unique run identifier | `session_state.json`, `summary.md`, `trace.jsonl` |
| `SessionState.target_file` | `str` | Controller | Frontend, summary, evaluation | Source file under debug | `session_state.json`, `summary.md` |
| `SessionState.max_attempts` | `int` | Controller | Controller, frontend, evaluation | Retry budget | `session_state.json`, `summary.md` |
| `SessionState.timeout_seconds` | `int` | Controller | Executor, summary | Execution bound | `session_state.json` |
| `SessionState.status` | `str` | Controller | Frontend, evaluation | Lifecycle status such as `running`, `fixed`, `stopped_no_patch` | `session_state.json`, `summary.md` |
| `SessionState.started_at` | `str` | Controller | Summary, frontend | Start timestamp | `session_state.json` |
| `SessionState.original_execution` | `ExecutionResult` | Executor through Controller | Diagnoser, Verifier, frontend, evaluation | Initial failure evidence | `session_state.json` |
| `SessionState.expected_output` | `str | None` | Controller | Verifier, frontend, evaluation | Optional behavior oracle | `session_state.json` |
| `SessionState.attempts` | `list[AttemptRecord]` | Controller | Legacy readers, summary | Compact attempt history | `session_state.json` |
| `SessionState.attempt_details` | `list[dict]` | Controller | Frontend, evaluation, summary | Full diagnosis, patch, rerun, verifier artifacts | `session_state.json` |
| `SessionState.trace_events_path` | `str | None` | Controller | Frontend, evaluation | Path to handoff trace | `session_state.json`, `summary.md` |
| `SessionState.final_message` | `str` | Controller | Summary, frontend | Human-readable final rationale | `session_state.json`, `summary.md` |
| `SessionState.trace_path` | `str | None` | Logger | Frontend, evaluation | Path to state snapshot | `session_state.json`, `summary.md` |
| `SessionState.saved_patch_path` | `str | None` | Controller | Frontend, evaluation | Accepted final patch path | `session_state.json`, `summary.md` |
| `SessionState.summary_path` | `str | None` | Controller | Frontend, evaluation | Markdown session summary | `session_state.json`, evaluation CSV |
| `SessionState.failure_summary_path` | `str | None` | Controller | Frontend, evaluation | Unresolved-case write-up | `session_state.json`, `summary.md` |
| `SessionState.intermediate_patch_paths` | `list[str]` | Controller | Frontend, summary | Patch candidates and diffs per attempt | `session_state.json`, `summary.md` |
| `SessionState.final_decision` | `str | None` | Verifier through Controller | Frontend, evaluation | `accept`, `retry`, `escalate`, or `stop` | `session_state.json`, `summary.md` |
| `SessionState.behavior_match_status` | `str | None` | Verifier through Controller | Frontend, evaluation | Whether rerun matched expected behavior or lacked oracle | `session_state.json`, `summary.md` |
| `SessionState.handoff_count` | `int` | Controller | Frontend, summary | Count of trace handoff events | `session_state.json` |

## Component Result Objects

| Result object | Type file | Written by | Read by | Purpose |
|---|---|---|---|---|
| `ExecutionResult` | [src/tracefix/types.py](/Users/macbook/Desktop/agentic/src/tracefix/types.py) | Executor | Diagnoser, Verifier, Controller | Captures stdout, stderr, traceback, timeout, failure line, and outcome label. |
| `DiagnoserResult` | [src/tracefix/types.py](/Users/macbook/Desktop/agentic/src/tracefix/types.py) | Diagnoser | Patcher, Controller, Frontend | Captures bug class, root-cause hypothesis, localized region, repair hints, confidence, provider metadata. |
| `PatcherResult` | [src/tracefix/types.py](/Users/macbook/Desktop/agentic/src/tracefix/types.py) | Patcher | Executor rerun, Verifier, Controller | Captures updated code, diff, changed regions, strategy, minimality, confidence, provider metadata. |
| `VerifierResult` | [src/tracefix/types.py](/Users/macbook/Desktop/agentic/src/tracefix/types.py) | Verifier | Controller, Frontend, Evaluation | Captures decision, rationale, regression flags, behavior match, retry feedback. |

## Write Permissions

| Component | Writes | Does not write |
|---|---|---|
| Executor | `ExecutionResult`, execution start/end/block trace events | Diagnosis, patch, verifier decision, session final status |
| Diagnoser | `DiagnoserResult` | Source files, patch artifacts, verifier decision |
| Patcher | `PatcherResult` | Final acceptance, retry budget, original execution evidence |
| Verifier | `VerifierResult` | Code edits, provider config, sandbox policy |
| Controller | `SessionState`, attempt history, final status, trace handoffs, summaries, patch artifact files | Raw provider responses beyond structured metadata |
| Frontend | Browser state only | Repository source code, controller state, evaluation CSVs |

## Why Stateless Agents and Stateful Controller

The stateless-agent pattern keeps each component easy to test and audit. Each worker receives a typed request and returns a typed result. The Controller is the only component that decides what happens next, which prevents hidden retry loops or state mutation inside the Diagnoser/Patcher/Verifier.

This design supports Phase 3 evidence requirements because every important transition can be reconstructed from `trace.jsonl`, `session_state.json`, and `summary.md`.

## Retry Memory

`prior_patch_history` and `prior_verifier_feedback` are passed into later Diagnoser/Patcher calls. They help prevent repeated failed strategies by making previous patch summaries and verifier feedback visible during the next attempt. The Controller owns these lists and appends to them only after an attempt has been verified or rejected.
