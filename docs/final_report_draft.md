# Final Report Draft

## Problem and User

Beginner-to-intermediate Python users often need help debugging one small script, not a whole repository. A common failure is a `NameError` where a variable is referenced before it is assigned. A generic coding assistant may rewrite the entire function, remove the crash, and leave the learner unable to tell whether the new behavior is correct or simply different.

TraceFix addresses this by keeping the workflow evidence-first and bounded: run the code, diagnose the observed failure, patch minimally, rerun, verify, and log the evidence.

## Architecture and Design Choices

TraceFix uses five core components:

- `Executor`: bounded local Python execution and evidence capture
- `Diagnoser`: localized root-cause hypothesis
- `Patcher`: minimal patch proposal or refusal
- `Verifier`: independent accept/retry/escalate/stop decision
- `Controller`: session state, retries, artifact persistence, and final status

The architecture is intentionally local-first. Optional OpenAI and Anthropic provider integrations can assist Diagnoser and Patcher, but Verifier remains deterministic-first and the Controller remains the authority over final decisions.

See:

- [docs/architecture_overview.md](docs/architecture_overview.md)
- [docs/model_and_provider_policy.md](docs/model_and_provider_policy.md)
- [docs/state_schema.md](docs/state_schema.md)

## Implementation Summary

The implementation includes:

- typed request/result objects
- bounded subprocess execution in a temporary working directory
- lightweight policy checks for out-of-scope execution patterns
- provider wrappers for OpenAI and Anthropic
- conservative local diagnoser and patcher logic
- deterministic verifier logic
- per-session artifacts and JSONL handoff traces
- evaluation runner and frontend visual demo layer

## Evaluation Setup

The final evaluation suite includes 7 single-file Python cases covering:

- syntax error
- name error
- argument mismatch
- missing resource
- unsupported runtime exception
- superficial fix / false-positive acceptance risk
- ambiguous behavior / no-oracle escalation

The runner writes root-level and timestamped artifacts:

- [evaluation/test_cases.csv](evaluation/test_cases.csv)
- [evaluation/evaluation_results.csv](evaluation/evaluation_results.csv)
- [evaluation/failure_log.md](evaluation/failure_log.md)
- [evaluation/runs/20260425T180442Z](evaluation/runs/20260425T180442Z)

## Results

Final run summary:

- Total cases: 7
- Accepted bounded repairs: 4
- Conservative stops: 2
- Escalations: 1
- Cases matching expected governance decision: 7

These results show both useful repair behavior and deliberate non-acceptance where evidence is weak.

## Failure Analysis

The most important failure/governance cases are:

- `bug_case_06_failure_superficial_fix`: a patch removes the crash but produces `HELLO, TRACEFIX!` instead of `Hello, TraceFix!`; the verifier rejects acceptance because the expected output does not match.
- `bug_case_07_failure_ambiguous_behavior`: a patch removes the crash and prints `17`, but no expected output is available; the verifier escalates rather than auto-accepting.

See:

- [evaluation/failure_log.md](evaluation/failure_log.md)
- [docs/phase3_failure_analysis.md](docs/phase3_failure_analysis.md)

## Governance and Safety Reflection

TraceFix is a lightweight course sandbox, not a hardened security boundary. It uses subprocess timeouts, temporary working directories, isolated Python mode, bytecode suppression, and static policy checks for common out-of-scope patterns. It also avoids internet access, package installation, and multi-file debugging during the debugging loop.

The most important governance decision is the verifier's refusal to equate "no crash" with "correct." This reduces false-positive acceptance risk and makes the system easier to defend in a course setting.

## Lessons Learned and Future Work

Lessons:

- separating patching from verification makes failure analysis clearer
- explicit expected output greatly improves acceptance confidence
- no-oracle cases should be escalated, not accepted by default
- local artifacts make the system easier to review and demo

Future work:

- add a few more bounded patch strategies
- add richer test oracle support
- improve generated failure summaries
- capture final screenshots and video evidence
- complete individual contribution reflections
