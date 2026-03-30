# Diagnoser Notes

## What the Diagnoser Does

The TraceFix diagnoser interprets executor evidence and turns it into a bounded repair hypothesis. It does not change code. It explains what failure class is most likely, where the likely cause is localized, what evidence supports that claim, and how confident the system should be before handing work to the patcher.

Its inputs include:

- current code
- latest `ExecutionResult`
- optional user intent
- optional expected output
- prior patch history
- prior verifier feedback
- session state summary

Its outputs include:

- primary bug class
- likely root cause
- localized code region
- evidence summary
- recommended repair direction
- confidence score and confidence band
- uncertainty notes
- up to two alternative hypotheses

## How Diagnosis Differs from Patching

Diagnosis answers "what most likely went wrong and where should we look first?" Patching answers "what concrete code change should we try next?" The diagnoser should narrow the search space and explain the evidence, while the patcher should stay conservative and operate only on the bounded repair direction it receives.

## Grounding in Execution Evidence

The diagnoser must be grounded in the latest executor record. It should cite:

- the outcome label
- the exception type
- the exception message
- the localized line from the current code

This keeps the diagnosis auditable and avoids inventing hidden dependencies, missing packages, or multi-file context that the current project scope does not support.

## Uncertainty Representation

TraceFix represents uncertainty explicitly rather than hiding it. Each diagnosis includes:

- a numeric confidence score
- a confidence band (`low`, `medium`, or `high`)
- uncertainty notes
- optional alternative hypotheses

This is important because some failures are directly observable, like syntax errors, while others only reveal a downstream symptom, such as a type mismatch caused by an earlier bad value.

## Deterministic Fallback

The current diagnoser includes a deterministic rule-based path for obvious cases:

- syntax errors
- name errors
- import errors
- missing file/resource failures
- argument mismatch patterns
- common runtime exceptions

This allows the prototype to remain usable even without depending on an LLM for every diagnosis. A structured prompt template is still included so the architecture is ready for a future model-backed path.

## Effect of Prior Failed Patches

Failed prior patches matter because they reduce confidence in repeating the same repair direction. The diagnoser uses prior patch history and verifier feedback to add uncertainty notes such as:

- do not repeat the same failed repair direction without new evidence
- a one-line explanation may be too weak if earlier attempts already failed verification

This helps the next component avoid overcommitting to an explanation that the system has already tested unsuccessfully.

## Current Limitations

- The current diagnoser is intentionally narrow and single-file only.
- Localization is strongest when the executor provides a precise failing line.
- Simple logic mismatches are only diagnosed when explicit expected output evidence exists.
- The prompt template is included for architecture completeness, but the current implementation relies on deterministic heuristics rather than a live model call.
