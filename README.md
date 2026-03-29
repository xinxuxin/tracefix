# TraceFix

TraceFix is a Track A course project scaffold for a conservative multi-agent Python debugging system. It focuses on one real and narrow user problem: helping beginner-to-intermediate Python users debug a single small script without requiring internet access, package installation during debugging, or unsafe autonomous shell behavior.

This repository is intentionally CLI-first and local-only. It is scoped to single-file Python debugging only.

## Project Purpose

TraceFix demonstrates how a small agentic system can coordinate bounded execution, diagnosis, patch generation, and verification for simple Python failures while leaving a clear audit trail for course reviewers.

## Scoped Problem

The system targets short Python scripts that fail with beginner-to-intermediate bug classes. The goal is not full autonomous repair. The goal is a narrow, explainable workflow that:

1. runs a script safely in a bounded local subprocess
2. interprets the failure
3. proposes one conservative patch
4. verifies whether the observed crash is removed
5. logs the handoffs, stopping conditions, and outputs

## Target User

The primary user is a beginner-to-intermediate Python learner who has a single `.py` file that crashes and needs help understanding what happened and whether a minimal patch candidate works.

## Architecture Overview

The architecture maps directly to the required system components:

- `Executor`: runs the script in isolated, bounded Python execution
- `Diagnoser`: maps an observed failure to a narrow supported bug class or an explicit stop
- `Patcher`: generates one conservative patch candidate
- `Verifier`: reruns the patched script and decides whether the original failure was resolved
- `Controller`: manages retries, state, handoffs, traces, and stopping conditions

The source layout keeps these concerns visible:

- runtime code under `src/tracefix/`
- architecture-aligned source buckets under `src/tracefix/agents/`, `src/tracefix/orchestrator/`, and `src/tracefix/sandbox/`
- evaluation artifacts under `evaluation/`
- demo cases under `cases/`
- trace logs under `logs/`
- saved patch outputs under `outputs/`

## Repository Layout

```text
.
├── .env.example
├── README.md
├── cases/
├── config/
├── docs/
├── evaluation/
├── logs/
│   └── traces/
├── outputs/
│   └── patches/
├── prompts/
├── pyproject.toml
├── scripts/
├── src/
│   └── tracefix/
│       ├── __init__.py
│       ├── __main__.py
│       ├── agents/
│       ├── cli.py
│       ├── config.py
│       ├── controller.py
│       ├── diagnoser.py
│       ├── executor.py
│       ├── logger.py
│       ├── models.py
│       ├── orchestrator/
│       ├── patcher.py
│       ├── sandbox/
│       ├── state.py
│       ├── types.py
│       └── verifier.py
└── tests/
```

## Python Version and Dependencies

- Python 3.11 target
- Minimal dependencies
- Standard library only in the current scaffold
- No web app
- Local CLI-first workflow

The dependency declaration lives in [pyproject.toml](/Users/macbook/Desktop/agentic/pyproject.toml). No separate `requirements.txt` is needed for this stage.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Run Commands

Run the CLI on a sample case:

```bash
python -m tracefix debug cases/name_error_bug.py
```

Run with an explicit config file:

```bash
python -m tracefix debug cases/missing_colon_bug.py --config config/settings.example.json
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Logs and Outputs

- JSON execution traces live under `logs/traces/`
- saved patch artifacts live under `outputs/patches/`
- evaluation templates live under `evaluation/`
- screenshot index and reviewer-facing visual evidence live under `docs/`

These locations are intentionally easy to inspect so a course reviewer can follow system behavior without reading every source file first.

## Example Artifacts

- Example trace: [logs/traces/example_trace_name_error.json](/Users/macbook/Desktop/agentic/logs/traces/example_trace_name_error.json)
- Example saved patch: [outputs/patches/example_fixed_name_error.py](/Users/macbook/Desktop/agentic/outputs/patches/example_fixed_name_error.py)
- Demo cases:
  - [cases/name_error_bug.py](/Users/macbook/Desktop/agentic/cases/name_error_bug.py)
  - [cases/missing_colon_bug.py](/Users/macbook/Desktop/agentic/cases/missing_colon_bug.py)
  - [cases/type_error_bug.py](/Users/macbook/Desktop/agentic/cases/type_error_bug.py)

## Assumptions

- Input is exactly one Python source file
- The debugging target does not require package installation during the debug session
- The system is allowed to execute bounded local Python subprocesses only
- Verification means checking whether the observed crash is removed, not proving full semantic correctness
- Retries remain bounded and conservative
- The user can inspect generated logs and outputs locally

## What Is Out of Scope

- Multi-file repositories
- Dependency installation during debugging
- Web UI or hosted service deployment
- Internet-dependent tools
- Autonomous shell behavior beyond bounded Python execution
- Hidden environment assumptions
- Broad semantic program repair
- High-risk patching without clear evidence

## Planned Evidence Package

The final course submission should include:

- traces and structured logs from real runs
- evaluation result files
- documented failure cases and failure analysis
- screenshots indexed in `docs/screenshot_index_template.md`
- an AI usage log showing prompts, manual edits, and independent verification

## Notes on Scope

This repository intentionally stays narrow. The current working prototype handles only a small set of conservative bug classes and stops explicitly when a fix cannot be justified.
