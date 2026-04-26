# TraceFix: A Multi-Agent Python Debugging System with Sandboxed Execution and Patch Verification

TraceFix is a CLI-first course project that demonstrates a narrow, auditable agentic workflow for debugging single-file Python scripts. The system runs buggy code in bounded local execution, diagnoses the observed failure, synthesizes a conservative patch, reruns the patched script, and then verifies whether the result should be accepted, retried, escalated, or stopped. The repository supports two operating styles: a fully local deterministic mode, and an optional API-enhanced mode where the Diagnoser and Patcher can call an external model provider while the Controller, Executor, Verifier, traces, evaluation, and artifacts all remain local and inspectable. This repository also includes an optional local visual frontend that sits on top of the existing controller and saved artifacts so reviewers can inspect handoffs, traces, patch diffs, verifier decisions, and evaluation outcomes without changing the underlying debugging scope.

## Target User

TraceFix is designed for beginner-to-intermediate Python users who are debugging one small `.py` file at a time and need help understanding a failure without relying on package installation, internet access, or broad autonomous shell behavior.

Concrete scenario: a student writes a short script that raises `NameError` because a variable is referenced before it is assigned. A generic AI coding tool might rewrite the whole function and leave the student unsure whether the new behavior is correct. TraceFix instead runs the script, records the failing line, diagnoses the undefined name, proposes a minimal patch, reruns the result, verifies expected behavior when available, and saves the evidence.

## Why This Is Agentic

TraceFix is agentic because it is not a single one-shot prompt that jumps directly from code to “final answer.” Instead, it uses distinct components with separate responsibilities, explicit handoffs, bounded retries, and stopping conditions:

- `Executor` gathers evidence from bounded execution.
- `Diagnoser` turns evidence into a localized repair hypothesis.
- `Patcher` proposes the smallest reasonable code edit.
- `Verifier` decides whether that patch should be accepted, retried, escalated, or stopped.
- `Controller` manages session state, artifacts, retries, and governance.

That separation makes the behavior easier to inspect, easier to evaluate, and safer to explain in a technical course setting.

The visual frontend does not replace this architecture. It is only a thin presentation layer over the same controller, session artifacts, and evaluation outputs.

API enhancement also does not replace this architecture. It is an optional improvement path for the Diagnoser and Patcher only, with explicit fallback to local logic when credentials, SDKs, or provider responses are unavailable.

## Architecture Overview

Core components:

- `Executor`
  - Runs the current script in bounded local Python execution.
  - Captures structured evidence: exit code, stdout, stderr, traceback, timeout, duration, and outcome label.
- `Diagnoser`
  - Interprets execution evidence.
  - Produces a localized bug hypothesis, repair direction, confidence level, and uncertainty notes.
  - Can run in local rules mode or optional provider-backed mode.
- `Patcher`
  - Synthesizes the smallest reasonable patch from the diagnosis.
  - Produces updated code, diff, changed regions, and patch confidence.
  - Can run in local template/rule mode or optional provider-backed mode.
- `Verifier`
  - Compares original and rerun behavior.
  - Decides `accept`, `retry`, `escalate`, or `stop`.
  - Remains rules-first and local, even when provider mode is enabled elsewhere.
- `Controller`
  - Orchestrates the workflow, persists artifacts, and enforces bounded retries and stopping conditions.
- `Visual API` (optional local adapter)
  - Exposes a tiny local HTTP interface for the demo frontend.
  - Calls the existing controller and reads existing session/evaluation artifacts.
- `Frontend` (optional local demo layer)
  - Visualizes agent handoffs, traces, patch diffs, verifier decisions, sample cases, and evaluation outputs.

See [architecture_overview.md](/Users/macbook/Desktop/agentic/docs/architecture_overview.md) for the detailed handoff design.

Provider and model policy:

- default mode is `local`
- optional OpenAI Diagnoser/Patcher model: `gpt-4.1`
- optional Anthropic Diagnoser/Patcher model: `claude-3-5-sonnet-latest`
- API temperature: `0.0`
- max output tokens: `1200`
- provider fallback: local rules when keys, SDKs, requests, or responses fail
- Verifier remains deterministic-first

See [model_and_provider_policy.md](/Users/macbook/Desktop/agentic/docs/model_and_provider_policy.md) and [state_schema.md](/Users/macbook/Desktop/agentic/docs/state_schema.md).

## Repository Tree

```text
tracefix/
├── .env.example
├── README.md
├── cases/
│   ├── README.md
│   ├── bug_case_01_syntax_error.py
│   ├── bug_case_02_name_error.py
│   ├── bug_case_03_argument_mismatch.py
│   ├── bug_case_04_missing_file.py
│   ├── bug_case_05_runtime_exception.py
│   ├── bug_case_06_failure_superficial_fix.py
│   ├── bug_case_07_failure_ambiguous_behavior.py
│   └── ...
├── config/
│   └── settings.example.json
├── docs/
│   ├── architecture_overview.md
│   ├── core_flow_walkthrough.md
│   ├── final_submission_checklist.md
│   ├── frontend_demo_notes.md
│   ├── governance_and_risks.md
│   ├── run_instructions.md
│   ├── failure_analysis_seed_notes.md
│   └── screenshot_index_template.md
├── evaluation/
│   ├── ai_usage_log_template.md
│   ├── evaluation_plan.md
│   ├── failure_log_template.csv
│   ├── results_template.csv
│   └── run_evaluation.py
├── logs/
│   └── traces/
├── outputs/
│   ├── patches/
│   └── sessions/
├── frontend/
│   ├── package.json
│   ├── src/
│   └── ...
├── scripts/
│   └── run_demo_case.py
├── src/
│   └── tracefix/
│       ├── agents/
│       ├── orchestrator/
│       ├── sandbox/
│       ├── utils/
│       ├── cli.py
│       ├── config.py
│       ├── controller.py
│       ├── logger.py
│       ├── state.py
│       ├── types.py
│       └── visual_api.py
└── tests/
```

## Setup Instructions

Python target:

- Python `3.11`

Minimal setup:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Optional API provider extras:

```bash
python -m pip install -e ".[openai]"
python -m pip install -e ".[anthropic]"
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

More detailed commands are collected in [run_instructions.md](/Users/macbook/Desktop/agentic/docs/run_instructions.md).

## Environment and Config Notes

- Default runtime settings live in [config/settings.example.json](/Users/macbook/Desktop/agentic/config/settings.example.json).
- Optional environment variables are documented in [.env.example](/Users/macbook/Desktop/agentic/.env.example).
- The system is local-only and does not require external services.
- Session artifacts are written per run so that traces are easy to inspect afterward.
- The frontend is optional and local-only. It is intended for demos, screenshots, and walkthroughs, not as a replacement for the CLI.
- API mode is optional. If no API key is configured, TraceFix still runs in local mode and does not crash.
- API keys should be supplied as environment variables only. Do not hardcode them and do not commit them to GitHub.
- If provider mode is enabled in an interactive terminal and the matching API key is missing, the CLI will prompt once with hidden input for the current session only.

## How To Run a Single Case

Run one case with inline expected output:

```bash
python -m tracefix debug cases/bug_case_02_name_error.py --expected-output-text "10.70"
```

Run one case with an explicit config file:

```bash
python -m tracefix debug cases/bug_case_04_missing_file.py --config config/settings.example.json --expected-output-text "Guest"
```

Run the demo script:

```bash
PYTHONPATH=src python3 scripts/run_demo_case.py
```

## How To Run in Local Mode

Local mode is the default:

```bash
python -m tracefix debug cases/bug_case_02_name_error.py --expected-output-text "10.70"
```

In this mode, Diagnoser and Patcher use the existing deterministic logic and no external provider is required.

## How To Run in OpenAI-Enhanced Mode

Install the optional SDK and set credentials:

```bash
python -m pip install -e ".[openai]"
export OPENAI_API_KEY=your_key_here
export TRACEFIX_PROVIDER_MODE=openai
export TRACEFIX_ENABLE_LLM_DIAGNOSER=1
export TRACEFIX_ENABLE_LLM_PATCHER=1
```

If you do not export `OPENAI_API_KEY` first, the CLI will securely prompt for it at run time in interactive use and keep it only in the current process environment.

Then run the same CLI flow:

```bash
python -m tracefix debug cases/bug_case_02_name_error.py --expected-output-text "10.70"
```

Default OpenAI model:

- `gpt-4.1`

You can override it with:

```bash
export TRACEFIX_PROVIDER_MODEL=gpt-4.1-mini
```

## How To Run in Anthropic-Enhanced Mode

Install the optional SDK and set credentials:

```bash
python -m pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY=your_key_here
export TRACEFIX_PROVIDER_MODE=anthropic
export TRACEFIX_ENABLE_LLM_DIAGNOSER=1
export TRACEFIX_ENABLE_LLM_PATCHER=1
```

If you do not export `ANTHROPIC_API_KEY` first, the CLI will securely prompt for it at run time in interactive use and keep it only in the current process environment.

Then run:

```bash
python -m tracefix debug cases/bug_case_04_missing_file.py --expected-output-text "Guest"
```

Default Anthropic model:

- `claude-3-5-sonnet-latest`

## How To Run the Visual Frontend

Development mode:

1. Start the local API adapter:

```bash
PYTHONPATH=src python -m tracefix visual-server --port 8123
```

2. In another terminal, install frontend dependencies and start Vite:

```bash
cd frontend
npm install
npm run dev
```

3. Open the local frontend shown by Vite, usually:

```text
http://127.0.0.1:5173
```

For the 5-minute Phase 3 recording, use the main page. It now includes the full video roadmap, workflow, evidence, evaluation, and final artifact sections:

```text
http://127.0.0.1:5173/
```

Built static mode:

```bash
cd frontend
npm install
npm run build
cd ..
PYTHONPATH=src python -m tracefix visual-server --port 8123
```

If `frontend/dist/` exists, `tracefix visual-server` will automatically serve it.

Built main demo URL:

```text
http://127.0.0.1:8123/
```

## How To Run Evaluation

Run the full evaluation package:

```bash
PYTHONPATH=src python3 evaluation/run_evaluation.py
```

The final Phase 3 evidence run is checked in under:

- [evaluation/evaluation_results.csv](/Users/macbook/Desktop/agentic/evaluation/evaluation_results.csv)
- [evaluation/failure_log.md](/Users/macbook/Desktop/agentic/evaluation/failure_log.md)
- [evaluation/baseline_comparison.csv](/Users/macbook/Desktop/agentic/evaluation/baseline_comparison.csv)
- [evaluation/runs/20260425T180442Z](/Users/macbook/Desktop/agentic/evaluation/runs/20260425T180442Z)

Summary of that run:

- 7 executed cases
- 4 accepted bounded repairs
- 2 conservative stops
- 1 no-oracle escalation
- 7 of 7 cases matched the expected governance decision

Run selected cases only:

```bash
PYTHONPATH=src python3 evaluation/run_evaluation.py \
  --case-id bug_case_02_name_error \
  --case-id bug_case_06_failure_superficial_fix
```

## Where Traces, Logs, and Results Are Saved

Single interactive debug session outputs:

- per-session controller artifacts under `outputs/sessions/<case>_<session_id>/`
- intermediate patch diffs under `outputs/sessions/<case>_<session_id>/patches/`
- accepted final patch under `outputs/sessions/<case>_<session_id>/final_patched_script.py`
- session summary under `outputs/sessions/<case>_<session_id>/summary.md`
- handoff trace under `outputs/sessions/<case>_<session_id>/trace.jsonl`

Visual frontend:

- reads the latest session from `outputs/sessions/`
- reads the latest evaluation run from `evaluation/runs/`
- does not replace or relocate those artifacts

Provider traceability:

- diagnoser and patcher results record whether they ran in `local`, `openai`, or `anthropic` mode
- session artifacts record provider name, model name, fallback usage, and provider errors when fallback occurs
- handoff traces include provider metadata for `diagnoser -> controller` and `patcher -> controller`

Evaluation outputs:

- run-level results under `evaluation/runs/<timestamp>/evaluation_results.csv`
- failure subset under `evaluation/runs/<timestamp>/failure_cases.csv`
- run summary under `evaluation/runs/<timestamp>/run_summary.md`
- case-specific session artifacts under `evaluation/runs/<timestamp>/cases/<case_id>/`

## Scoped Boundaries

TraceFix is intentionally narrow:

- single-file Python scripts only
- beginner-to-intermediate bug classes only
- no internet access
- no package installation during debugging
- no multi-file repository reasoning
- bounded retries with conservative stopping

The optional frontend does not widen the debugging scope. It is only a local visualization and demo surface over the same single-file workflow.
Optional API enhancement also does not widen the scope. It only changes how Diagnoser and Patcher generate their bounded outputs.

Sandbox note: TraceFix uses a lightweight course sandbox based on temporary working directories, bounded subprocess execution, isolated Python mode, timeout enforcement, and a static policy gate for common out-of-scope patterns. It is not a hardened security boundary for adversarial code. See [governance_and_risks.md](/Users/macbook/Desktop/agentic/docs/governance_and_risks.md) and [executor_notes.md](/Users/macbook/Desktop/agentic/docs/executor_notes.md).

## Phase 3 Submission Evidence

Key final-submission files:

- [AI_USAGE.md](/Users/macbook/Desktop/agentic/AI_USAGE.md)
- [docs/ai_prompt_appendix.md](/Users/macbook/Desktop/agentic/docs/ai_prompt_appendix.md)
- [docs/ai_logs/](/Users/macbook/Desktop/agentic/docs/ai_logs)
- [docs/final_report_draft.md](/Users/macbook/Desktop/agentic/docs/final_report_draft.md)
- [docs/phase3_submission_checklist.md](/Users/macbook/Desktop/agentic/docs/phase3_submission_checklist.md)
- [docs/phase3_validation_report.md](/Users/macbook/Desktop/agentic/docs/phase3_validation_report.md)
- [docs/phase3_workplan.md](/Users/macbook/Desktop/agentic/docs/phase3_workplan.md)
- [docs/screenshots/screenshot_index.md](/Users/macbook/Desktop/agentic/docs/screenshots/screenshot_index.md)
- [media/demo_video_link.txt](/Users/macbook/Desktop/agentic/media/demo_video_link.txt)

## Known Limitations

- Behavioral verification is strongest only when expected output is available.
- The patcher intentionally refuses many broader runtime or semantic issues.
- The sandbox is lightweight and course-appropriate, not a hardened security boundary.
- TraceFix does not currently attempt broad logic repair or multi-file fixes.
- Some successful reruns are escalated rather than accepted when the verifier lacks a strong behavior oracle.
- The optional visual layer is optimized for local demos and screenshots, not for deployment or multi-user use.
- API mode depends on optional SDK installation and environment variables; when those are missing or fail, the system falls back to local logic.
- Runtime prompting is session-only convenience, not persistent secret storage.

## Suggested Demo Cases

Best happy-path demo cases:

- [bug_case_02_name_error.py](/Users/macbook/Desktop/agentic/cases/bug_case_02_name_error.py)
- [bug_case_04_missing_file.py](/Users/macbook/Desktop/agentic/cases/bug_case_04_missing_file.py)

Best retry / governance demos:

- [bug_case_06_failure_superficial_fix.py](/Users/macbook/Desktop/agentic/cases/bug_case_06_failure_superficial_fix.py)
- [bug_case_07_failure_ambiguous_behavior.py](/Users/macbook/Desktop/agentic/cases/bug_case_07_failure_ambiguous_behavior.py)

Best conservative-stop demo:

- [bug_case_05_runtime_exception.py](/Users/macbook/Desktop/agentic/cases/bug_case_05_runtime_exception.py)

Recommended frontend screenshot path:

- Hero + architecture summary
- Animated pipeline after a successful run
- Trace timeline
- Patch diff view
- Verifier result panel
- Evaluation dashboard with the two failure cases visible

See [run_instructions.md](/Users/macbook/Desktop/agentic/docs/run_instructions.md) and [frontend_demo_notes.md](/Users/macbook/Desktop/agentic/docs/frontend_demo_notes.md) for the fastest demo path.
