# Patcher Notes

## What the Patcher Does

The TraceFix patcher turns a bounded diagnosis into the smallest reasonable code edit it can justify. It does not execute the code and it does not decide final acceptance. Its job is to synthesize one conservative candidate patch and make that patch transparent through a readable diff and explicit changed regions.

Its outputs include:

- updated code
- patch diff
- changed regions
- patch summary
- intended effect
- minimality flag
- confidence score
- refusal reason when the patch is too uncertain

## Minimal Edit Philosophy

The patcher is designed around minimal edits. It prefers:

- one-line syntax fixes
- localized identifier corrections
- small call-site repairs
- narrow resource guards

It avoids whole-program rewrites because broad edits are harder to trust, harder to review, and more likely to hide the real cause of failure.

## How It Differs from Diagnoser and Verifier

The diagnoser explains what likely went wrong and where. The patcher proposes a concrete code edit based on that diagnosis. The verifier then reruns the program and checks whether the patch actually improved the observed behavior.

This separation matters because:

- diagnosis should stay evidence-first
- patching should stay edit-first
- verification should stay outcome-first

Keeping these concerns separate makes the system easier to audit and easier to explain in a course project.

## Safeguards

The current patcher includes simple safeguards:

- reject empty updated code
- reject accidental massive truncation
- flag patch size as `minimal`, `moderate`, or `broad`
- refuse low-confidence patches without localized repair hints
- discourage repeating the same failed patch strategy on retries

These safeguards are intentionally conservative. Refusing a patch is better than pretending certainty and damaging unrelated code.

## Known Failure Modes

The current patcher can still fail in several ways:

- superficial patching that fixes the symptom but not the real cause
- over-editing when a deterministic rule touches more lines than intended
- placeholder-style fixes for argument or file-path cases that may not reflect user intent
- inability to patch cases that need semantic understanding beyond local evidence

For that reason, the patcher records both a diff artifact and a confidence score, so later components and reviewers can see exactly what changed and why.
