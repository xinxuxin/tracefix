# Project Video Speech Notes

These notes match the actual TraceFix main page at `http://127.0.0.1:8123/`. The recording should stay on the main page and use its section navigation: `Video Roadmap`, `Workspace`, `Pipeline`, `Explorer`, `Evaluation`, and `Final Output`.

## 0:00-0:30 Problem and Target User

Open the main page and start on the hero plus `Video Roadmap`.

Speech:

"TraceFix is built for beginner-to-intermediate Python users who are debugging small, single-file scripts. The core problem is not just that code crashes. The harder problem is that an AI-generated patch can look plausible while only hiding the crash or changing the intended behavior. TraceFix keeps the task narrow: single-file Python, bounded retries, local artifacts, no internet during debugging, and a verifier that checks behavior instead of accepting a no-crash result."

Show:

- Hero problem statement and target user cards.
- Scope chips: single-file Python, rules-first verifier, bounded retries, local artifacts, no internet during debugging.
- `Video Roadmap` section showing the full five-minute flow.

## 0:30-1:10 Architecture

Stay near the hero, then move to `Pipeline`.

Speech:

"The architecture is separated into five responsibilities. The Controller owns the session lifecycle, retry budget, and final status. The Executor runs the submitted script in bounded local execution and records facts. The Diagnoser interprets the failure from evidence. The Patcher proposes the smallest reasonable edit. The Verifier reruns the evidence and decides whether to accept, retry, escalate, or stop. This separation matters because TraceFix is not a general autonomous coding agent. It is an auditable workflow where each component leaves traceable evidence."

Show:

- Hero system strip.
- `Pipeline View` with Controller, Executor, Diagnoser, Patcher, Verifier.
- Current session bar with handoff count and retry count.

## 1:10-2:30 Main Workflow From Beginning To End

Go to `Workspace`.

Speech:

"For the main workflow, I use the happy-path case `bug_case_02_name_error.py`. This is a small script with a runtime name error, and the expected output is `10.70`. I load the sample case, keep the expected output as the behavior oracle, and click `Run TraceFix`. The controller starts the session, the executor captures the original failure, the diagnoser identifies the root cause, the patcher creates a minimal edit, the executor reruns the patched script, and the verifier only accepts if the expected behavior matches."

Show:

- Sample case selector with `bug_case_02_name_error.py`.
- Python code editor and expected output field.
- `Run TraceFix` button.
- `Pipeline View` after the run.
- `Verification Result` final decision, original failure resolved, behavior match, retry count.

## 2:30-3:20 Evidence Layer

Go to `Explorer`.

Speech:

"The main value of TraceFix is the evidence layer. After a run, the frontend exposes the trace timeline, patch diff, retry attempts, and saved artifacts. The trace shows component coordination and handoffs. The diff shows what changed. The verifier panel explains why the final decision was accepted, retried, escalated, or stopped. The artifact tab points to local files like `trace.jsonl`, `session_state.json`, `summary.md`, and the final patched script."

Show:

- `Trace timeline` tab and expand at least one event payload.
- `Patch diff` tab with split or unified diff.
- `Patch attempts` tab if retries exist.
- `Artifacts` tab with trace, summary, state snapshot, final patch paths.

## 3:20-4:20 Failure, Limitation, Or Boundary Behavior

Go to `Evaluation`, then focus on `Failure Analysis`.

Speech:

"TraceFix is designed to be conservative. Two failure cases are especially important for Phase 3. In the superficial-fix case, a patch may remove the immediate crash but still fail the intended behavior, so the verifier should not accept it. In the ambiguous behavior case, the script may run, but there is no strong oracle proving correctness, so TraceFix escalates or stops rather than pretending that no crash means success. These boundary cases show why the verifier is necessary."

Show:

- Failure Analysis cards.
- `bug_case_06_failure_superficial_fix`.
- `bug_case_07_failure_ambiguous_behavior`.
- Evaluation table rows for stop/escalate outcomes.

## 4:20-5:00 Evaluation And Final Output

End on `Evaluation`, then `Final Output`.

Speech:

"For evaluation, the repository includes seven executed cases, including happy-path, governance, and failure or boundary scenarios. The dashboard summarizes accepted, stopped, and escalated outcomes, plus retries and artifact-backed evidence. The final output is not just a patched file. It is the whole evidence package: evaluation CSV, failure log, trace JSONL, session state, summary markdown, final patch when accepted, final report draft, and the Phase 3 checklist. The contribution is a runnable local multi-component debugging system that makes patch verification visible and auditable."

Show:

- Evaluation metrics: total cases, accepted, stopped, escalated, average retries.
- Evaluation table.
- `Final Output & Evidence Package` cards.
- Manual submission note: screenshots/video link still require team capture and are not fabricated by the app.

## Closing Line

"TraceFix demonstrates a narrow but auditable agentic debugging workflow: run, diagnose, patch, rerun, verify, and preserve evidence so users can understand whether a patch is actually correct."
