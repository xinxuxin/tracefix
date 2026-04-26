# AI Usage Disclosure

## 1. Project Metadata

| Field | Value |
|---|---|
| Project name | TraceFix: A Multi-Agent Python Debugging System with Sandboxed Execution and Patch Verification |
| Course | 94815 Agentic Technologies, CMU Heinz College |
| Track | Track A: Technical Build |
| Team members | Siru Tao, Xin Xu, Fan Yang, Crystal Huang |
| AI usage disclosure owner | Xin Xu |
| Reviewers | Siru Tao, Fan Yang, Crystal Huang |
| Disclosure scope | Phases 1-3 (scoping/canvas; architecture/prototype/evaluation plan; final submission package) |

## 2. Purpose of Disclosure

This disclosure explains how the TraceFix team used AI tools while planning, building, documenting, evaluating, and preparing the Phase 1, Phase 2, and Phase 3 course deliverables and submission materials. AI tools were used as assistants for project comparison, scoping, architecture drafting, coding support, frontend design support, evaluation planning, failure-analysis wording, README/report planning, and compliance checking.

The team remained responsible for final project direction, final scope boundaries, architecture approval, code review, running actual tests and evaluation cases, checking trace/session artifacts, selecting screenshots, final video recording, and final submission decisions.

## 3. Summary Table of Tools Used

| Tool name and version | Used for | Type of assistance | Final use in project | Human verification performed |
|---|---|---|---|---|
| ChatGPT GPT-5.4 | Project idea comparison, Track A selection, scoping, architecture explanation, README/report wording | Planning, drafting, explanation, critique | Used to shape project framing and documentation drafts | Team reviewed scope, checked claims against the repository, and retained final decision authority |
| ChatGPT GPT-5.5 Thinking | Phase 3 feedback repair planning, compliance checking, documentation drafting, evaluation package planning | Deep reasoning, audit support, structured documentation | Used to produce and revise compliance docs and submission checklists | Repository files were inspected; evaluation/tests/builds were run locally; unsupported claims were removed or marked as missing evidence |
| Claude Code | Code-oriented planning and implementation support | Coding assistant / repository task support | Used as a development-time assistant where team members chose to apply suggestions | Team reviewed code changes and ran tests before accepting repository behavior |
| Google Gemini | Brainstorming, review, wording, alternative framing | Ideation and writing support | Used for comparison, critique, and documentation phrasing | Team checked final wording against TraceFix scope and implementation |
| MiniMax | Drafting, brainstorming, and written explanation support | Writing and planning support | Used for supplemental drafting of project explanations or report language | Team edited final language and removed unsupported claims |
| Grok | Brainstorming, alternative critiques, and planning support | Ideation and review support | Used for supplemental comparison and planning | Team made final decisions and checked claims against repository evidence |
| OpenAI Codex / coding assistant | Repository construction support, code edits, frontend visualization improvement, evaluation runner updates, Phase 3 compliance documentation | Coding, refactoring support, documentation generation, local command execution | Used to prepare repository changes and documentation now present in the project | Unit tests, evaluation runner, frontend build, trace/session artifact inspection, and documentation-vs-code consistency checks were performed |

## 4. AI Use by Project Area

### Project Scoping and Track A Selection

Tools used:

- ChatGPT GPT-5.4
- ChatGPT GPT-5.5 Thinking
- Google Gemini
- MiniMax
- Grok

What AI helped generate:

- comparisons between possible project ideas
- arguments for choosing Track A technical build
- early problem framing for a single-file Python debugging assistant
- explanations of why a multi-component debugging workflow could count as agentic
- draft wording for the one-paragraph project summary and scoping/justification narrative used in the Phase 1 submission PDF
- initial drafts of the "multi-agent system canvas" and "agent canvas" descriptions used in the Phase 1 submission, later rewritten and edited by the team

What the team changed manually:

- selected the final TraceFix project direction
- constrained the scope to single-file beginner/intermediate Python bugs
- rejected broader multi-file repository debugging and autonomous shell workflows
- decided that conservative stopping and verifier authority were core project values
- edited/reorganized the scoping writeup in the Phase 1 deliverable to match the team's intended scope and evidence boundaries

What the team independently verified:

- project scope against course requirements
- feasibility against available implementation time
- alignment between final scope and sample cases
- whether the implemented system actually included separable Executor, Diagnoser, Patcher, Verifier, and Controller roles

### Agentic Architecture and Role Design

Tools used:

- ChatGPT GPT-5.4
- ChatGPT GPT-5.5 Thinking
- Claude Code
- OpenAI Codex / coding assistant

What AI helped generate:

- multi-agent system canvas drafts
- individual component role descriptions
- architecture explanation language
- handoff and state-management documentation
- suggestions for provider-backed Diagnoser/Patcher modes
- initial role writeups for Executor/Diagnoser/Patcher/Verifier/Controller used to seed the Agent Canvas in the Phase 1 submission
- wording drafts for the architecture diagram description, role definitions, and coordination logic narrative included in the Phase 2 report

What the team changed manually:

- approved the final five-component architecture
- kept the Controller as the only owner of session lifecycle and retry state
- kept the Verifier rules-first and evidence-based
- kept runtime scope bounded to single-file Python scripts
- kept optional LLM provider support separate from the deterministic core

What the team independently verified:

- component behavior in `src/tracefix/agents/`
- state schema in `src/tracefix/state.py` and `src/tracefix/types.py`
- orchestration behavior in `src/tracefix/orchestrator/controller.py`
- trace and session artifact generation under `outputs/` and `evaluation/runs/`

### Code Implementation and Repository Support

Tools used:

- Claude Code
- OpenAI Codex / coding assistant
- ChatGPT GPT-5.5 Thinking

What AI helped generate:

- code scaffolding suggestions
- provider abstraction and fallback design suggestions
- environment-variable API key handling suggestions
- evaluation runner field expansion suggestions
- lightweight sandbox policy documentation and test suggestions

What the team changed manually:

- reviewed and accepted code changes
- preserved CLI commands and frontend commands
- kept API keys out of config and repository files
- kept local deterministic mode as the default
- avoided widening the debugging scope

What the team independently verified:

- Python unit tests with `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- evaluation runner with `PYTHONPATH=src python3 evaluation/run_evaluation.py`
- frontend build with `npm run build`
- whitespace check with `git diff --check`
- generated traces, `session_state.json`, `summary.md`, patch diffs, and final evaluation CSVs

### Frontend Visualization and UI Improvement

Tools used:

- ChatGPT GPT-5.4
- ChatGPT GPT-5.5 Thinking
- OpenAI Codex / coding assistant
- Google Gemini

What AI helped generate:

- frontend visualization planning
- UI hierarchy suggestions
- interaction ideas for trace, diff, verifier, evaluation, and artifact views
- wording for frontend demo notes
- screenshot checklist structure

What the team changed manually:

- selected final demo flow
- kept the frontend as a local visualization layer only
- preserved backend contracts and existing visual API data flow
- selected which screenshots and video sections should represent the project

What the team independently verified:

- frontend local build
- frontend API compatibility through existing visual service tests
- that the frontend still represents sample cases, run results, trace timeline, patch diff, verifier decision, evaluation dashboard, and failure-analysis sections

### Evaluation and Failure Analysis

Tools used:

- ChatGPT GPT-5.5 Thinking
- OpenAI Codex / coding assistant
- Google Gemini

What AI helped generate:

- evaluation plan structure
- failure-analysis categories
- baseline comparison framing
- suggested CSV columns for Phase 3 evidence
- narrative language explaining false-positive acceptance risk and no-oracle escalation
- evaluation plan outline and success metric wording used in the Phase 2 deliverable, later revised based on actual prototype behavior

What the team changed manually:

- ran actual evaluation cases
- kept failed/governance cases in the evidence package
- selected the final evaluation run used in the repository
- interpreted results based on generated artifacts rather than AI claims

What the team independently verified:

- 7 executed evaluation cases in `evaluation/evaluation_results.csv`
- at least two failure/governance cases in `evaluation/failure_log.md`
- trace paths, session state paths, summaries, patch diffs, and final decisions
- baseline comparison in `evaluation/baseline_comparison.csv`

### Final Report, README, and Submission Package

Tools used:

- ChatGPT GPT-5.4
- ChatGPT GPT-5.5 Thinking
- Google Gemini
- MiniMax
- Grok
- OpenAI Codex / coding assistant

What AI helped generate:

- README wording
- final report draft sections
- submission checklist structure
- workplan table
- AI usage disclosure draft
- model/provider policy wording
- state schema and governance documentation wording

What the team changed manually:

- selected final claims
- preserved course-specific scope
- decided which artifacts support final evidence
- prepared final report and video materials for review

What the team independently verified:

- documentation links to actual repository files
- evaluation claims are backed by actual CSVs and session artifacts
- runtime provider values match `config/settings.example.json` and `src/tracefix/config.py`
- remaining missing evidence is called out instead of invented

## 5. Runtime AI Model Use

TraceFix has two categories of AI use:

- development-time AI assistance used by the team while building and documenting the project
- optional runtime LLM provider support inside the TraceFix system

Runtime component policy:

- Executor is deterministic and local.
- Controller is deterministic orchestration and state management.
- Verifier is rules-first and evidence-based.
- Diagnoser may use optional LLM assistance if provider mode and component flags are enabled.
- Patcher may use optional LLM assistance if provider mode and component flags are enabled.
- The project remains bounded, evidence-driven, and single-file only.

Actual repository configuration found in `config/settings.example.json` and `src/tracefix/config.py`:

| Runtime setting | Configured value |
|---|---:|
| Default provider mode | `local` |
| OpenAI model if enabled | `gpt-4.1` |
| Anthropic model if enabled | `claude-3-5-sonnet-latest` |
| API temperature | `0.0` |
| API timeout | `20` seconds |
| API max tokens | `1200` |
| LLM Diagnoser enabled by default | `false` |
| LLM Patcher enabled by default | `false` |
| LLM Verifier assist enabled by default | `false` |
| Fallback to local on provider error | `true` |

Phase 2 prototype demos and the submitted Phase 3 evaluation evidence were produced in local deterministic mode. Optional provider configuration is documented in `docs/model_and_provider_policy.md`.

## 6. Exact Prompts and Full Responses

Exact prompt records and response locations are recorded in `docs/ai_prompt_appendix.md`.

Large exported AI responses and conversation logs should be stored under `docs/ai_logs/`. At the time this disclosure package was generated, the repository did not contain full exported response logs for all listed AI tools. This is a compliance warning: before final submission, the team should attach exported logs or update the appendix to point to the official exported transcript location.

This disclosure does not fabricate missing full AI responses.

## 7. Manual Review and Independent Verification

The team used the following review and verification methods:

- code review before accepting implementation changes
- Python unit tests
- CLI and evaluation-run execution
- frontend local build
- trace inspection
- session artifact inspection
- patch diff inspection
- documentation-vs-code consistency checks
- scope verification against the stated single-file debugging boundary
- review of verifier decisions to ensure TraceFix does not accept merely because a script no longer crashes

Known validation artifacts:

- `docs/phase3_validation_report.md`
- `evaluation/evaluation_results.csv`
- `evaluation/failure_log.md`
- `evaluation/baseline_comparison.csv`
- `evaluation/runs/20260425T180442Z/`

## 8. AI-Generated Versus Team-Controlled Work

AI-assisted:

- idea comparisons
- draft wording
- prompt drafts
- architecture explanation drafts
- code scaffolding suggestions
- frontend design suggestions
- evaluation structure
- failure-analysis structure
- README/report/submission package planning

Team-controlled:

- final project direction
- final scope
- final architecture approval
- actual implementation acceptance
- running tests
- interpreting results
- final report claims
- final submission package
- screenshot selection
- final video recording

## 9. Known Limitations of AI-Assisted Work

- AI may generate plausible but incorrect code.
- AI may overstate capabilities unless claims are checked against implementation.
- AI documentation may not match the repository unless reviewed against source files.
- AI-generated patches can remove crashes without restoring intended behavior.
- Evaluation claims must come from actual runs, not generated prose.
- AI tools cannot supply missing team-specific evidence unless conversation exports are attached.

TraceFix specifically addresses one of these limitations through its Verifier: it does not accept a patch simply because the patched script no longer crashes.

## 10. Team Responsibility Statement

All team members are responsible for the final submitted TraceFix work. AI outputs were treated as assistance, not as authoritative project decisions. The team reviewed, edited, tested, and verified the submitted repository artifacts and remains responsible for the accuracy of final claims, evaluation evidence, report content, and submission materials.
