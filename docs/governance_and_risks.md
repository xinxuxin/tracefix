# Governance and Risks

## Scope Limits

TraceFix is intentionally constrained to:

- single-file Python debugging
- beginner-to-intermediate bug classes
- bounded local execution
- bounded retries
- conservative patching

It is not intended for:

- multi-file repositories
- dependency management
- production-grade autonomous debugging
- broad semantic program repair

## Safety Boundaries

TraceFix includes several deliberate boundaries:

- no internet access assumptions
- no automatic package installation
- no hidden repository context
- no arbitrary shell behavior beyond bounded Python invocation
- timeout-based execution bounds
- refusal and escalation when evidence is weak

These boundaries reduce accidental scope expansion and make system behavior easier to justify in a course setting.

## Trust Concerns

The main trust concern is false-positive acceptance: a patch may remove the crash without preserving intended behavior.

TraceFix reduces that risk by:

- separating verification from patch generation
- using expected output when available
- escalating when behavior cannot be trusted automatically
- stopping when retries are exhausted or patch evidence is weak

## Ambiguity Handling

When user intent or expected behavior is unclear, TraceFix should not pretend certainty.

Instead, it should:

- record uncertainty explicitly
- avoid broad speculative edits
- escalate rather than auto-accept

This is especially important for cases where execution succeeds after patching but no reliable behavior oracle exists.

## Misuse Risks

Possible misuse or over-claim risks include:

- presenting the system as a general autonomous debugger
- assuming it can safely handle arbitrary user code
- using it for multi-file or internet-dependent projects outside scope
- over-trusting accepted patches without reviewing evidence

The documentation and evaluation package should make these limits explicit.

## Why TraceFix Does Not Install Packages, Access the Internet, or Debug Multi-File Systems

These exclusions are deliberate governance choices:

- package installation would widen scope and hide environmental assumptions
- internet access would reduce reproducibility and introduce uncontrolled dependencies
- multi-file debugging would require broader repository reasoning, dependency tracking, and higher-risk patching

By refusing those behaviors, TraceFix remains narrow, auditable, and aligned with its course-project goals.
