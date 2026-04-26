# Screenshot Index

This folder contains the Phase 3 UI and workflow screenshots for TraceFix. These screenshots support the final report by showing the final artifact, main user workflow, evidence layer, evaluation dashboard, failure/boundary cases, and submission-ready outputs.

## Screenshot Files

| File | Caption |
|---|---|
| `01_home_landing.jpg` | TraceFix frontend landing screen showing the project purpose, local visual demo layer, component sequence, target user, and scoped debugging workflow. |
| `02_main_interaction.jpg` | Main workspace where users select a sample case, inspect or paste a single-file Python script, provide expected output, set retry limits, and run TraceFix. |
| `03_demo_case_controls.jpg` | Quick-load demo scenario controls grouped by happy path, governance, and failure/stop cases, showing settings, controls, and scenario selection for walkthrough and evaluation review. |
| `04_component_decision_view.jpg` | Component handoff and final decision view showing Controller, Executor, Diagnoser, Patcher, and Verifier outputs for an accepted repair case. |
| `05_trace_diff_artifacts.jpg` | Session explorer showing trace timeline, patch diff, patch attempts, and artifact tabs used as the evidence layer for post-hoc review. |
| `06_evaluation_failure_dashboard.jpg` | Evaluation dashboard showing total cases, accepted cases, stopped cases, escalated cases, outcome distribution, and two high-value limitation stories. |
| `07_final_output_evidence_package.jpg` | Final output and evidence package view showing the latest evaluation run, evaluation results CSV, failure log, trace JSONL, session state, final patch, report draft, and submission checklist. |

## Coverage of Screenshot Requirements

| Requirement | Covered By |
|---|---|
| Home or landing screen | `01_home_landing.jpg` |
| Main interaction screen | `02_main_interaction.jpg` |
| Evidence, citation, or source view | `05_trace_diff_artifacts.jpg` |
| Saved thread, history, or state view if relevant | `05_trace_diff_artifacts.jpg` |
| Artifact generation or export screen | `07_final_output_evidence_package.jpg` |
| Evaluation or results screen | `06_evaluation_failure_dashboard.jpg` |
| One image showing a failure case or boundary case | `06_evaluation_failure_dashboard.jpg` |
| One image showing settings, controls, or filters if relevant | `03_demo_case_controls.jpg` |
