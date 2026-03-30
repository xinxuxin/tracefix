# Verifier Notes

## Why the Verifier Is a Separate Component

The verifier exists because removing a crash is not the same as proving a fix is correct. A patch can make the script run without actually preserving the intended behavior. The verifier therefore acts as a separate governance step between patch generation and final acceptance.

Its role is to compare:

- original execution evidence
- rerun execution evidence after patching
- optional expected output
- optional simple test information
- patch breadth and retry context

From that comparison it decides whether the system should accept, retry, escalate, or stop.

## False-Positive Acceptance Risk

The main verifier risk is false-positive acceptance: the script no longer crashes, but the behavior is still wrong. To reduce that risk, the verifier:

- does not accept only because the rerun exits successfully
- uses expected output when available
- flags suspicious behavior changes when no explicit oracle exists
- considers broad patches lower-trust than minimal patches

This makes acceptance more conservative and more defensible in a course project setting.

## Retry, Escalate, and Stop

The verifier supports bounded control logic:

- `retry` when the original failure changed and a plausible next step remains
- `escalate` when human judgment is needed
- `stop` when retries are exhausted or the system is not learning anything new

This helps prevent endless loops and makes controller decisions easier to explain.

## Governance and Failure Analysis

The verifier is especially important for failure analysis because it records:

- whether the original failure was resolved
- whether behavior matched the available oracle
- regression flags
- targeted feedback for the next retry

These outputs help reviewers understand why the system accepted or refused a patch and provide clear evidence for later failure-analysis writeups.

## Current Limitations

- Behavioral checking is only strong when expected output or a clear oracle exists.
- The current simple test spec is lightweight and does not provide a full unit-test harness.
- The independent `VerifierAgent` is implemented, while the legacy controller path still uses a simpler compatibility verifier for now.
