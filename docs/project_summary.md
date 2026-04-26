# Project Summary

## Project

TraceFix is a multi-component debugging system for beginner-to-intermediate Python users who are working on one small script at a time. It runs the script, captures evidence, diagnoses the likely issue, proposes a bounded patch, reruns the patched script, and asks a verifier whether the patch should be accepted, retried, escalated, or stopped.

## Concrete Motivating Scenario

A student writes a small Python script that loops over values and prints a total, but the script raises a `NameError` because a variable is referenced before it is ever assigned. A generic AI coding tool might rewrite the whole function, rename several variables, or change the output format in a way that looks plausible but is hard for the student to trust.

TraceFix takes a narrower path. It executes the script first, records the traceback and failing line, diagnoses the undefined name, proposes the smallest likely rename or local repair, reruns the patched code, and only accepts the patch if the verifier has enough evidence that the behavior is correct.

## User and Scope

Target user:

- beginner-to-intermediate Python learner
- working on a single `.py` file
- needs help understanding a failure and reviewing evidence

Out of scope:

- multi-file repository debugging
- dependency installation during debugging
- internet access during debugging
- broad semantic program repair
- autonomous shell workflows

## Agentic Design

TraceFix is agentic because it separates responsibilities across inspectable components:

- Executor gathers execution evidence.
- Diagnoser turns evidence into a localized hypothesis.
- Patcher proposes a conservative patch.
- Verifier makes an independent decision.
- Controller owns state, retries, stopping, and artifacts.

The system is not a single prompt that jumps directly from code to answer. It records handoffs and preserves evidence so reviewers can see why the final decision happened.

## Final Evaluation Snapshot

The Phase 3 evaluation run executed 7 cases:

- 4 accepted bounded repairs
- 2 conservative stops
- 1 no-oracle escalation
- 7 of 7 cases matched the expected governance decision

Evidence:

- [evaluation/evaluation_results.csv](evaluation/evaluation_results.csv)
- [evaluation/failure_log.md](evaluation/failure_log.md)
- [evaluation/runs/20260425T180442Z](evaluation/runs/20260425T180442Z)

## Lessons and Next Steps

TraceFix works best when an expected output or simple behavior oracle exists. Without an oracle, it deliberately escalates instead of pretending that successful execution proves correctness.

Next improvements:

- add a few more safe patch strategies for common runtime exceptions
- improve behavior-level diagnosis when expected output is present
- add richer but still bounded test-oracle support
- capture final screenshots and a 5-minute demo video for submission
