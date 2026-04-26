# AI Prompt Appendix

This appendix records the major AI-assisted prompt/task records used for TraceFix. It is written for final submission review and focuses on prompt intent, what the team accepted, what the team changed manually, and what was independently verified.

Some early planning conversations were not exported as full response logs into this repository. For those entries, this appendix provides the final archived prompt/task text reconstructed from team notes, repository evidence, and the submitted project materials. The team should not treat these reconstructed records as a substitute for full exported response logs if the course platform separately requires complete AI response transcripts.

## Response Log Policy

Course policy asks for prompt records and full AI responses. This repository includes the prompt/task records below and the AI disclosure in `AI_USAGE.md`. Full exported response logs, if submitted, should be stored or referenced under `docs/ai_logs/` using the filenames described in `docs/ai_logs/README.md`.

No API keys, private tokens, or personal credentials should be included in any exported AI log.

## P001 — Track Selection and Project Idea Evaluation

| Field | Value |
|---|---|
| Prompt ID | P001 |
| Tool | ChatGPT GPT-5.4, Google Gemini, MiniMax, Grok |
| Purpose | Compare project ideas and choose a Track A technical build direction. |
| Prompt / task text | We are choosing a final project for 94815 Agentic Technologies. Compare possible Track A technical-build ideas for feasibility, course fit, demo value, and evaluation clarity. One candidate is a bounded multi-agent Python debugging system that runs a small single-file script, diagnoses the failure, proposes a conservative patch, reruns the code, and verifies whether the patch should be accepted, retried, escalated, or stopped. Recommend whether this idea is stronger than broader alternatives, identify the target user, define a narrow scope, and list risks that must be controlled for a final course submission. |
| Full response location | If exported, store under `docs/ai_logs/chatgpt_phase_planning_export.md`, `docs/ai_logs/gemini_review_notes.md`, `docs/ai_logs/minimax_drafting_notes.md`, or `docs/ai_logs/grok_brainstorming_notes.md`. |
| What the team changed manually afterward | Selected TraceFix as the final project, narrowed the scope to single-file Python debugging, and rejected broader autonomous repo-debugging scope. |
| What the team independently verified | Checked Track A fit, feasibility, course alignment, and final scope boundaries. |
| Final repository files affected | `README.md`, `docs/project_summary.md`, `docs/final_report_draft.md` |

## P002 — Phase 1 Scoping and Justification

| Field | Value |
|---|---|
| Prompt ID | P002 |
| Tool | ChatGPT GPT-5.4, ChatGPT GPT-5.5 Thinking |
| Purpose | Tighten the Phase 1 problem statement, user, project scope, and justification. |
| Prompt / task text | Help write a concise Phase 1 scope and justification for TraceFix, a Track A technical build for beginner-to-intermediate Python learners. The problem is that AI-generated code patches can look plausible while only hiding a crash or changing behavior. Use one concrete motivating example, such as a student script that raises a `NameError` because a variable was never assigned or was misspelled before use. Explain why a one-shot coding tool is insufficient, why a bounded multi-component workflow is appropriate, and what is explicitly out of scope: multi-file repositories, package installation, internet access, production repair, and broad autonomous shell behavior. |
| Full response location | If exported, store under `docs/ai_logs/chatgpt_phase_planning_export.md`. |
| What the team changed manually afterward | Added the concrete `NameError` student scenario and kept the user/scope focused on beginner-to-intermediate single-file Python debugging. |
| What the team independently verified | Checked that README/report claims match implemented sample cases and CLI behavior. |
| Final repository files affected | `README.md`, `docs/project_summary.md`, `docs/final_report_draft.md` |

## P003 — Multi-Agent System Canvas Generation

| Field | Value |
|---|---|
| Prompt ID | P003 |
| Tool | ChatGPT GPT-5.4, Claude Code, OpenAI Codex / coding assistant |
| Purpose | Draft multi-agent roles, handoffs, state flow, and governance structure. |
| Prompt / task text | Create a multi-agent system canvas for TraceFix. The system should debug only single-file Python scripts using bounded local execution. Define the Controller, Executor, Diagnoser, Patcher, and Verifier. Explain each component's responsibility, inputs, outputs, handoff points, stopping conditions, retry loop, and evidence artifacts. Include how session state is owned by the Controller while worker components remain mostly stateless. Add governance principles: conservative patching, bounded retries, no internet access during debugging, no package installation, no multi-file repository repair, and no acceptance merely because a script no longer crashes. |
| Full response location | If exported, store under `docs/ai_logs/chatgpt_phase_planning_export.md` or `docs/ai_logs/claude_code_task_log.md`. |
| What the team changed manually afterward | Approved the final Executor, Diagnoser, Patcher, Verifier, Controller architecture and kept the Controller as state owner. |
| What the team independently verified | Inspected `src/tracefix/orchestrator/controller.py`, `src/tracefix/state.py`, and generated trace/session artifacts. |
| Final repository files affected | `docs/architecture_overview.md`, `docs/state_schema.md`, `src/tracefix/orchestrator/controller.py` |

## P004 — Agent Canvas Generation

| Field | Value |
|---|---|
| Prompt ID | P004 |
| Tool | ChatGPT GPT-5.4, Claude Code, OpenAI Codex / coding assistant |
| Purpose | Draft individual component responsibilities for Executor, Diagnoser, Patcher, Verifier, and Controller. |
| Prompt / task text | Draft individual agent canvases for the TraceFix components: Controller, Executor, Diagnoser, Patcher, and Verifier. For each component, specify its goal, allowed actions, forbidden actions, inputs, outputs, failure modes, dependencies, logs, and tests. Make the Executor deterministic and sandboxed, the Diagnoser evidence-driven, the Patcher conservative and minimal, the Verifier independent and rules-first, and the Controller responsible for lifecycle, retry budget, final decision, and artifact persistence. |
| Full response location | If exported, store under `docs/ai_logs/chatgpt_phase_planning_export.md` or `docs/ai_logs/claude_code_task_log.md`. |
| What the team changed manually afterward | Preserved stateless component behavior and independent verifier authority. |
| What the team independently verified | Checked agent implementation and tests in `src/tracefix/agents/` and `tests/`. |
| Final repository files affected | `docs/diagnoser_notes.md`, `docs/patcher_notes.md`, `docs/verifier_notes.md`, `docs/executor_notes.md` |

## P005 — Repository Build Planning

| Field | Value |
|---|---|
| Prompt ID | P005 |
| Tool | OpenAI Codex / coding assistant, Claude Code |
| Purpose | Plan repository structure, CLI-first workflow, tests, traces, logs, and evaluation scaffolding. |
| Prompt / task text | Plan and scaffold a runnable repository for TraceFix without widening the project scope. Preserve the core identity: a CLI-first bounded agentic debugging system for single-file Python scripts. Include source modules for Controller, Executor, Diagnoser, Patcher, Verifier, typed state/results, provider abstractions, sample cases, tests, evaluation runner, run instructions, traces/logs/session artifacts, and documentation. Keep local deterministic mode as the default. Do not add authentication, databases, cloud sync, multi-file repo debugging, or unsafe autonomous shell behavior. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p005--repository-build-planning-and-implementation-support` |
| What the team changed manually afterward | Reviewed generated structure, kept existing CLI commands, ran tests, and preserved project scope. |
| What the team independently verified | Unit tests, evaluation runner, CLI runs, and session artifacts. |
| Final repository files affected | `src/tracefix/`, `tests/`, `evaluation/run_evaluation.py`, `docs/run_instructions.md` |

## P006 — Frontend Addition Prompt

| Field | Value |
|---|---|
| Prompt ID | P006 |
| Tool | OpenAI Codex / coding assistant, ChatGPT GPT-5.4 |
| Purpose | Add or plan the optional frontend visualization layer. |
| Prompt / task text | Add an optional local frontend visualization layer for TraceFix without replacing the CLI-first system or changing backend contracts. The frontend should help reviewers understand the project overview, debug workspace, pipeline handoffs, trace timeline, patch diff, verifier decision, sample cases, evaluation dashboard, failure analysis, session artifacts, and intermediate patch attempts. Use real local artifacts and the visual API where possible. Keep the frontend stable, locally runnable, and clearly scoped as a demo/evidence layer rather than a new product surface. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p006--frontend-addition-and-demo-layer-support` |
| What the team changed manually afterward | Kept the frontend as an optional local demo layer over existing controller/session/evaluation artifacts. |
| What the team independently verified | Frontend build, visual API tests, and frontend documentation. |
| Final repository files affected | `frontend/`, `src/tracefix/visual_api.py`, `docs/frontend_demo_notes.md` |

## P007 — Frontend Visual Improvement Prompt

| Field | Value |
|---|---|
| Prompt ID | P007 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Improve the existing frontend visual demo layer while preserving functionality and backend contracts. |
| Prompt / task text | You are my senior frontend engineer and UX implementation copilot. I already have a working TraceFix project and a working frontend visualization layer. Do not rebuild the project, redesign the core architecture, refactor the backend heavily, or change the debugging scope. Upgrade the existing frontend only so it looks more modern, clearer, more interactive, and more demo-ready while preserving current features: overview, debug workspace, dynamic pipeline, trace timeline, patch diff, verification result, sample cases, evaluation dashboard, failure analysis, session artifacts, intermediate patch attempts, and local Vite/visual API run mode. Remove the overly painterly look and move toward a crisp technical dashboard style with cool neutrals, clean borders, strong hierarchy, restrained shadows, Framer Motion animations, accessible contrast, stable local behavior, and documentation for demo screenshots. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p007--frontend-visual-improvement` |
| What the team changed manually afterward | Accepted frontend polish only after preserving existing features, keeping the local visual API contract, and verifying build stability. |
| What the team independently verified | `npm run build`, frontend docs, and visual API tests. |
| Final repository files affected | `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/tailwind.config.ts`, `docs/frontend_demo_notes.md` |

## P008 — Optional API / Hybrid Model Route Prompt

| Field | Value |
|---|---|
| Prompt ID | P008 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Add or refine optional provider-backed Diagnoser/Patcher behavior and safe API-key handling. |
| Prompt / task text | Make the optional API/provider route safer. API keys should be configurable through environment variables instead of hardcoded config. If a key is not present in config or the environment, ask at runtime only for the current session. Do not hardcode API keys and do not upload API keys to GitHub. Preserve local deterministic fallback, keep provider use limited to Diagnoser and Patcher, document OpenAI and Anthropic model settings, record provider metadata in traces without logging secrets, and report the current progress and code changes. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p008--optional-api-provider-and-api-key-safety` |
| What the team changed manually afterward | Kept API keys out of config and repository files, preserved local fallback, and documented optional provider behavior. |
| What the team independently verified | Provider fallback tests and runtime prompt tests. |
| Final repository files affected | `src/tracefix/providers/`, `src/tracefix/config.py`, `src/tracefix/cli.py`, `tests/test_provider_modes.py`, `tests/test_cli_runtime_prompt.py`, `docs/model_and_provider_policy.md` |

## P009 — Phase 3 Feedback Repair Prompt

| Field | Value |
|---|---|
| Prompt ID | P009 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Inspect the repository, fix Phase 1 and Phase 2 feedback, and prepare Phase 3 final submission evidence. |
| Prompt / task text | You are my senior engineer, documentation lead, and course-compliance auditor. I already have a working project called TraceFix: A Multi-Agent Python Debugging System with Sandboxed Execution and Patch Verification. This is a Track A technical build for 94815 Agentic Technologies. Do not rebuild the project, redesign from scratch, widen scope, or delete useful files. Inspect the repository, create a gap report, fix missing AI usage disclosure, run and document actual evaluation results, document at least two failure cases, add model/provider assignments, formalize state schema, specify sandbox enforcement, evidence the frontend, add baseline comparison, assign Phase 3 owners, tighten the problem statement with a concrete NameError scenario, update final report/checklist/docs, run tests/builds, and report remaining team-owned tasks honestly without fabricating results. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p009--phase-3-feedback-repair-and-compliance-package` |
| What the team changed manually afterward | Ran evaluation, inspected artifacts, kept failure cases honest, and marked missing team-owned materials as compliance warnings. |
| What the team independently verified | `PYTHONPATH=src python3 evaluation/run_evaluation.py`, `PYTHONPATH=src python -m unittest discover -s tests -v`, `npm run build`, `git diff --check`. |
| Final repository files affected | `AI_USAGE.md`, `docs/phase3_gap_report.md`, `docs/phase3_submission_checklist.md`, `docs/phase3_validation_report.md`, `evaluation/evaluation_results.csv`, `evaluation/failure_log.md` |

## P010 — AI Usage Disclosure Prompt

| Field | Value |
|---|---|
| Prompt ID | P010 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Generate a course-compliant AI usage disclosure package. |
| Prompt / task text | You are my Phase 3 compliance documentation assistant for the TraceFix project. I already have a working repository called TraceFix: A Multi-Agent Python Debugging System with Sandboxed Execution and Patch Verification. Generate a course-compliant AI usage disclosure package only; do not modify core source code, architecture, or evaluation results. Create or update `AI_USAGE.md`, `docs/ai_prompt_appendix.md`, `docs/ai_logs/README.md`, the Phase 3 checklist if needed, and README links if relevant. Include tools used, project areas, runtime model use, prompt records, manual changes, independent verification, limitations, and team responsibility. Do not invent fake AI usage details, fake logs, or fake full responses. If full responses are not available, point to the expected exported log location and keep the disclosure honest. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p010--ai-usage-disclosure-package` |
| What the team changed manually afterward | Reviewed the disclosure, removed non-English prompt text, and aligned the appendix with final submission evidence. |
| What the team independently verified | Repository search for existing AI/prompt evidence and consistency with known tool list supplied by the team. |
| Final repository files affected | `AI_USAGE.md`, `docs/ai_prompt_appendix.md`, `docs/ai_logs/README.md`, `docs/phase3_submission_checklist.md`, `README.md` |

## P011 — Final Demo, Screenshots, And Report Package Prompt

| Field | Value |
|---|---|
| Prompt ID | P011 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Verify final demo readiness, add video/screenshot/final-report artifacts, and prepare repository evidence for submission. |
| Prompt / task text | Act as senior QA engineer, frontend reviewer, demo director, and Phase 3 submission auditor for TraceFix. Verify that the project is runnable, that the frontend supports the final 5-minute demo requirements, that the evidence package includes at least five completed cases and at least two failure cases, and that screenshots, final report, demo video, AI usage disclosure, validation reports, and submission checklist are present. Do not fabricate screenshots, video links, AI logs, or evaluation results. Add the provided screenshot archive and final report PDF to the repository, remove non-English text from submission documents, verify the report matches the current repository version, and run validation commands before committing or pushing. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p011--final-demo-screenshots-report-and-github-evidence` |
| What the team changed manually afterward | Reviewed the final report quality check, confirmed screenshot filenames, and pushed the final evidence package to GitHub. |
| What the team independently verified | Non-English text scan, PDF text extraction, screenshot file existence, empty-file scan, `git diff --check`, Python unit tests, and frontend build. |
| Final repository files affected | `docs/final_report/`, `docs/screenshots/`, `docs/phase3_validation_report.md`, `docs/phase3_submission_checklist.md`, `README.md` |

## P012 — Final English-Only AI Log Export

| Field | Value |
|---|---|
| Prompt ID | P012 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Export the implementation portion of the active Codex conversation into the AI logs folder and remove non-English text. |
| Prompt / task text | Export the implementation part of the current conversation, remove all non-English text, place it in the GitHub AI logs folder, and upload it to GitHub. |
| Full response location | `docs/ai_logs/codex_repository_tasks_export.md#p012--final-english-only-ai-log-export` |
| What the team changed manually afterward | Reviewed the generated AI log for final-submission readability and verified that it does not include non-English text. |
| What the team independently verified | Non-English text scan, placeholder scan, and `git diff --check`. |
| Final repository files affected | `docs/ai_logs/codex_repository_tasks_export.md`, `docs/ai_prompt_appendix.md` |

## Final Submission Notes

- This appendix contains final prompt/task records in English and no non-English prompt text.
- The implementation-related Codex task export is stored in `docs/ai_logs/codex_repository_tasks_export.md`. If the course submission form requires additional raw transcripts from other tools, attach those exports separately under `docs/ai_logs/`.
- The team remains responsible for verifying that final claims match the code, tests, evaluation artifacts, screenshots, video, and final report.
