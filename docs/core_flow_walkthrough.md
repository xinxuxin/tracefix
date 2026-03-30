# Core Flow Walkthrough

This document describes the end-to-end TraceFix workflow for a single-file Python debugging session.

## Happy Path Demo

Recommended demo command:

```bash
PYTHONPATH=src python3 scripts/run_demo_case.py
```

The default demo case is `cases/name_error_bug.py` with expected output `Hello, TraceFix!`.

## What Each Component Does

1. `Controller`
   - Creates a session id and a per-session artifact folder under `outputs/sessions/`.
   - Initializes retry state and records handoff events.

2. `Executor`
   - Writes the current script version to a temporary file.
   - Runs bounded Python execution with a timeout.
   - Captures exit code, stdout, stderr, traceback, duration, and outcome label.

3. `Diagnoser`
   - Reads the latest execution evidence.
   - Produces a localized root-cause hypothesis and repair direction.

4. `Patcher`
   - Creates the smallest reasonable code edit from the diagnosis.
   - Produces updated code, changed regions, and a readable diff.

5. `Executor` again
   - Reruns the patched code in the same bounded style.

6. `Verifier`
   - Compares original vs rerun behavior.
   - Uses expected output when available.
   - Returns `accept`, `retry`, `escalate`, or `stop`.

7. `Controller`
   - Either finishes, retries with bounded state, or writes an unresolved failure summary.

## Where Logs Are Saved

Each session writes a dedicated folder like:

```text
outputs/sessions/name_error_bug_<session_id>/
├── final_patched_script.py
├── patches/
│   ├── attempt_01.diff
│   └── attempt_01_candidate.py
├── session_state.json
├── summary.md
└── trace.jsonl
```

If the case remains unresolved, the session folder also includes:

```text
failure_summary.md
```

## Why This Is Better Than a Single One-Shot Prompt

This workflow is easier to justify and review than a one-shot “fix my script” prompt because:

- execution evidence is captured before diagnosis
- every handoff is visible in `trace.jsonl`
- patch generation is bounded and localized
- acceptance is separated from patch generation
- retries stop after a fixed budget instead of looping indefinitely

That separation makes TraceFix more auditable, more course-ready, and easier to discuss in architecture and failure-analysis sections.
