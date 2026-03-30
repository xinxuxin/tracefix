# TraceFix: A Multi-Agent Python Debugging System with Sandboxed Execution and Patch Verification

TraceFix is a CLI-first course project that demonstrates a narrow, auditable agentic workflow for debugging single-file Python scripts. The system runs buggy code in bounded local execution, diagnoses the observed failure, synthesizes a conservative patch, reruns the patched script, and then verifies whether the result should be accepted, retried, escalated, or stopped. The repository is organized to be easy to run locally, easy to inspect for course reviewers, and easy to reuse in a final report or demo video.

## Target User

TraceFix is designed for beginner-to-intermediate Python users who are debugging one small `.py` file at a time and need help understanding a failure without relying on package installation, internet access, or broad autonomous shell behavior.

## Why This Is Agentic

TraceFix is agentic because it is not a single one-shot prompt that jumps directly from code to “final answer.” Instead, it uses distinct components with separate responsibilities, explicit handoffs, bounded retries, and stopping conditions:

- `Executor` gathers evidence from bounded execution.
- `Diagnoser` turns evidence into a localized repair hypothesis.
- `Patcher` proposes the smallest reasonable code edit.
- `Verifier` decides whether that patch should be accepted, retried, escalated, or stopped.
- `Controller` manages session state, artifacts, retries, and governance.

That separation makes the behavior easier to inspect, easier to evaluate, and safer to explain in a technical course setting.

## Architecture Overview

Core components:

- `Executor`
  - Runs the current script in bounded local Python execution.
  - Captures structured evidence: exit code, stdout, stderr, traceback, timeout, duration, and outcome label.
- `Diagnoser`
  - Interprets execution evidence.
  - Produces a localized bug hypothesis, repair direction, confidence level, and uncertainty notes.
- `Patcher`
  - Synthesizes the smallest reasonable patch from the diagnosis.
  - Produces updated code, diff, changed regions, and patch confidence.
- `Verifier`
  - Compares original and rerun behavior.
  - Decides `accept`, `retry`, `escalate`, or `stop`.
- `Controller`
  - Orchestrates the workflow, persists artifacts, and enforces bounded retries and stopping conditions.

See [architecture_overview.md](/Users/macbook/Desktop/agentic/docs/architecture_overview.md) for the detailed handoff design.

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
│       └── types.py
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

## How To Run Evaluation

Run the full evaluation package:

```bash
PYTHONPATH=src python3 evaluation/run_evaluation.py
```

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
- no web app or web server
- no multi-file repository reasoning
- bounded retries with conservative stopping

## Known Limitations

- Behavioral verification is strongest only when expected output is available.
- The patcher intentionally refuses many broader runtime or semantic issues.
- The sandbox is lightweight and course-appropriate, not a hardened security boundary.
- TraceFix does not currently attempt broad logic repair or multi-file fixes.
- Some successful reruns are escalated rather than accepted when the verifier lacks a strong behavior oracle.

## Suggested Demo Cases

Best happy-path demo cases:

- [bug_case_02_name_error.py](/Users/macbook/Desktop/agentic/cases/bug_case_02_name_error.py)
- [bug_case_04_missing_file.py](/Users/macbook/Desktop/agentic/cases/bug_case_04_missing_file.py)

Best retry / governance demos:

- [bug_case_06_failure_superficial_fix.py](/Users/macbook/Desktop/agentic/cases/bug_case_06_failure_superficial_fix.py)
- [bug_case_07_failure_ambiguous_behavior.py](/Users/macbook/Desktop/agentic/cases/bug_case_07_failure_ambiguous_behavior.py)

Best conservative-stop demo:

- [bug_case_05_runtime_exception.py](/Users/macbook/Desktop/agentic/cases/bug_case_05_runtime_exception.py)
