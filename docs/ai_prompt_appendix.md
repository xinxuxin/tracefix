# AI Prompt Appendix

This appendix records major AI-assisted prompt categories for TraceFix and points to the location of full AI responses where available. It is intentionally evidence-based. If a prompt or response log was not found in the repository, the record says so directly and instructs the team to attach the exported AI conversation log before final submission.

Searches performed for this appendix included repository matches for: `codex prompt`, `AI prompt`, `prompt appendix`, `phase prompt`, `frontend prompt`, `usage disclosure`, `TraceFix`, `GPT`, `Claude`, `Gemini`, `MiniMax`, `Grok`, `Codex`, and `ChatGPT`.

## Response Log Policy

Course policy requires exact prompts and the AI tool's full response in an appendix. The repository currently contains prompt summaries and some task prompts in conversation context, but it does not contain full exported response logs for every listed AI tool.

Full response source for missing entries: exported AI conversation log to be submitted in `docs/ai_logs/`.

Do not treat "not found in repository" entries as complete until the team attaches exported logs.

## P001 — Track Selection and Project Idea Evaluation

| Field | Value |
|---|---|
| Prompt ID | P001 |
| Tool | ChatGPT GPT-5.4, Google Gemini, MiniMax, Grok |
| Purpose | Compare project ideas and choose Track A technical build direction. |
| Exact prompt | Not found in repository; team should attach exported AI conversation log before final submission. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/chatgpt_phase_planning_export.md`, `docs/ai_logs/gemini_review_notes.md`, `docs/ai_logs/minimax_drafting_notes.md`, or `docs/ai_logs/grok_brainstorming_notes.md`. |
| What the team changed manually afterward | Selected TraceFix as the final project, narrowed the scope to single-file Python debugging, and rejected broader autonomous repo-debugging scope. |
| What the team independently verified | Checked Track A fit, feasibility, course alignment, and final scope boundaries. |
| Final repository files affected | `README.md`, `docs/project_summary.md`, `docs/final_report_draft.md` |

## P002 — Phase 1 Scoping and Justification

| Field | Value |
|---|---|
| Prompt ID | P002 |
| Tool | ChatGPT GPT-5.4, ChatGPT GPT-5.5 Thinking |
| Purpose | Tighten problem statement, user, scope, and project justification. |
| Exact prompt | Not found in repository; team should attach exported AI conversation log before final submission. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/chatgpt_phase_planning_export.md`. |
| What the team changed manually afterward | Added the concrete `NameError` student scenario and kept the user/scope focused on beginner-to-intermediate single-file Python debugging. |
| What the team independently verified | Checked that README/report claims match implemented sample cases and CLI behavior. |
| Final repository files affected | `README.md`, `docs/project_summary.md`, `docs/final_report_draft.md` |

## P003 — Multi-Agent System Canvas Generation

| Field | Value |
|---|---|
| Prompt ID | P003 |
| Tool | ChatGPT GPT-5.4, Claude Code, OpenAI Codex / coding assistant |
| Purpose | Draft multi-agent roles, handoffs, state flow, and governance structure. |
| Exact prompt | Not found in repository; team should attach exported AI conversation log before final submission. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/chatgpt_phase_planning_export.md` or `docs/ai_logs/claude_code_task_log.md`. |
| What the team changed manually afterward | Approved the final Executor, Diagnoser, Patcher, Verifier, Controller architecture and kept the Controller as state owner. |
| What the team independently verified | Inspected `src/tracefix/orchestrator/controller.py`, `src/tracefix/state.py`, and generated trace/session artifacts. |
| Final repository files affected | `docs/architecture_overview.md`, `docs/state_schema.md`, `src/tracefix/orchestrator/controller.py` |

## P004 — Agent Canvas Generation

| Field | Value |
|---|---|
| Prompt ID | P004 |
| Tool | ChatGPT GPT-5.4, Claude Code, OpenAI Codex / coding assistant |
| Purpose | Draft individual component responsibilities for Executor, Diagnoser, Patcher, Verifier, and Controller. |
| Exact prompt | Not found in repository; team should attach exported AI conversation log before final submission. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/chatgpt_phase_planning_export.md` or `docs/ai_logs/claude_code_task_log.md`. |
| What the team changed manually afterward | Preserved stateless component behavior and independent verifier authority. |
| What the team independently verified | Checked agent implementation and tests in `src/tracefix/agents/` and `tests/`. |
| Final repository files affected | `docs/diagnoser_notes.md`, `docs/patcher_notes.md`, `docs/verifier_notes.md`, `docs/executor_notes.md` |

## P005 — Repository Build Planning

| Field | Value |
|---|---|
| Prompt ID | P005 |
| Tool | OpenAI Codex / coding assistant, Claude Code |
| Purpose | Plan repository structure, CLI-first workflow, tests, traces, logs, and evaluation scaffolding. |
| Exact prompt | Not found in repository; team should attach exported AI conversation log before final submission. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/codex_repository_tasks_export.md` or `docs/ai_logs/claude_code_task_log.md`. |
| What the team changed manually afterward | Reviewed generated structure, kept existing CLI commands, ran tests, and preserved project scope. |
| What the team independently verified | Unit tests, evaluation runner, CLI runs, and session artifacts. |
| Final repository files affected | `src/tracefix/`, `tests/`, `evaluation/run_evaluation.py`, `docs/run_instructions.md` |

## P006 — Frontend Addition Prompt

| Field | Value |
|---|---|
| Prompt ID | P006 |
| Tool | OpenAI Codex / coding assistant, ChatGPT GPT-5.4 |
| Purpose | Add or plan the optional frontend visualization layer. |
| Exact prompt | Not found in repository; team should attach exported AI conversation log before final submission. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/codex_repository_tasks_export.md`. |
| What the team changed manually afterward | Kept the frontend as an optional local demo layer over existing controller/session/evaluation artifacts. |
| What the team independently verified | Frontend build, visual API tests, and frontend documentation. |
| Final repository files affected | `frontend/`, `src/tracefix/visual_api.py`, `docs/frontend_demo_notes.md` |

## P007 — Frontend Visual Improvement Prompt

| Field | Value |
|---|---|
| Prompt ID | P007 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Improve the existing frontend visual demo layer while preserving functionality and backend contracts. |
| Exact prompt | The conversation included a detailed prompt beginning: "You are my senior frontend engineer and UX implementation copilot. I already have a working TraceFix project and a working frontend visualization layer. Do NOT rebuild the project. Do NOT redesign the core architecture. Do NOT refactor the backend heavily. Do NOT change the debugging scope." Full prompt text is not stored as a repository file. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/codex_repository_tasks_export.md`. |
| What the team changed manually afterward | Accepted frontend polish only after preserving existing features, keeping the local visual API contract, and verifying build stability. |
| What the team independently verified | `npm run build`, frontend docs, and visual API tests. |
| Final repository files affected | `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/tailwind.config.ts`, `docs/frontend_demo_notes.md` |

## P008 — Optional API / Hybrid Model Route Prompt

| Field | Value |
|---|---|
| Prompt ID | P008 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Add or refine optional provider-backed Diagnoser/Patcher behavior and safe API-key handling. |
| Exact prompt | English translation of the repository conversation follow-up: "Make the API key configurable through environment variables for better security. If the config does not contain it, ask at runtime. Do not hardcode the API key and do not upload the API key to GitHub. Tell me the current progress and changes." Earlier full hybrid-provider prompt text was not found in repository files. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/codex_repository_tasks_export.md`. |
| What the team changed manually afterward | Kept API keys out of config and repository files, preserved local fallback, and documented optional provider behavior. |
| What the team independently verified | Provider fallback tests and runtime prompt tests. |
| Final repository files affected | `src/tracefix/providers/`, `src/tracefix/config.py`, `src/tracefix/cli.py`, `tests/test_provider_modes.py`, `tests/test_cli_runtime_prompt.py`, `docs/model_and_provider_policy.md` |

## P009 — Phase 3 Feedback Repair Prompt

| Field | Value |
|---|---|
| Prompt ID | P009 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Inspect the repository, fix Phase 1 and Phase 2 feedback, and prepare Phase 3 final submission evidence. |
| Exact prompt | The conversation included a detailed prompt beginning: "You are my senior engineer, documentation lead, and course-compliance auditor. I already have a working project called: TraceFix: A Multi-Agent Python Debugging System with Sandboxed Execution and Patch Verification. This is a Track A technical build for 94815 Agentic Technologies. Your task is NOT to rebuild the whole project." Full prompt text is not stored as a repository file. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/codex_repository_tasks_export.md`. |
| What the team changed manually afterward | Ran evaluation, inspected artifacts, kept failure cases honest, and marked missing team-owned materials as compliance warnings. |
| What the team independently verified | `PYTHONPATH=src python3 evaluation/run_evaluation.py`, `PYTHONPATH=src python3 -m unittest discover -s tests -v`, `npm run build`, `git diff --check`. |
| Final repository files affected | `AI_USAGE.md`, `docs/phase3_gap_report.md`, `docs/phase3_submission_checklist.md`, `docs/phase3_validation_report.md`, `evaluation/evaluation_results.csv`, `evaluation/failure_log.md` |

## P010 — AI Usage Disclosure Prompt

| Field | Value |
|---|---|
| Prompt ID | P010 |
| Tool | OpenAI Codex / coding assistant |
| Purpose | Generate a course-compliant AI usage disclosure package. |
| Exact prompt | The conversation included the exact prompt beginning: "You are my Phase 3 compliance documentation assistant for the TraceFix project. I already have a working repository called: TraceFix: A Multi-Agent Python Debugging System with Sandboxed Execution and Patch Verification. Your task is to generate a course-compliant AI usage disclosure package." The full current prompt is available in the active conversation transcript but is not stored as a separate repository file. |
| Full response location | Full response source: exported AI conversation log to be submitted in `docs/ai_logs/codex_repository_tasks_export.md`. |
| What the team changed manually afterward | This record should be reviewed after the team exports the final Codex conversation log. |
| What the team independently verified | Repository search for existing AI/prompt evidence and consistency with known tool list supplied by the team. |
| Final repository files affected | `AI_USAGE.md`, `docs/ai_prompt_appendix.md`, `docs/ai_logs/README.md`, `docs/phase3_submission_checklist.md`, `README.md` |

## Compliance Warnings

- Full AI responses for ChatGPT, Claude Code, Gemini, MiniMax, Grok, and Codex were not found as exported files in the repository.
- The team should export and attach full conversation logs before final submission if the course requires the AI tool's complete response text.
- Do not replace missing logs with reconstructed or invented responses.
- When exported logs are added, update the "Full response location" field for each prompt record.
