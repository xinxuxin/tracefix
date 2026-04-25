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
- local-first fallback when provider enhancement fails

These boundaries reduce accidental scope expansion and make system behavior easier to justify in a course setting.

## Sandbox Enforcement Details

TraceFix uses a lightweight course sandbox implemented in:

- [src/tracefix/sandbox/executor.py](/Users/macbook/Desktop/agentic/src/tracefix/sandbox/executor.py)
- [src/tracefix/sandbox/policy.py](/Users/macbook/Desktop/agentic/src/tracefix/sandbox/policy.py)

What is enforced in code:

- code is written to a temporary directory created with `tempfile.TemporaryDirectory`
- subprocess execution uses that temporary directory as `cwd`
- Python runs through the configured interpreter with isolated mode `-I` and bytecode writes disabled with `-B`
- every execution has a timeout, defaulting to 2 seconds in project config
- stdout, stderr, traceback, timeout, exit code, and outcome labels are captured into `ExecutionResult`
- policy-blocked code returns `blocked_by_policy` instead of crashing the controller
- trace events record execution start, execution end, and policy-blocked execution

Current static policy blocks common out-of-scope patterns:

- socket imports and simple network fetch patterns
- `requests` imports
- `subprocess` imports
- `os.system` and `os.popen`
- destructive filesystem helpers such as `os.remove`, `os.unlink`, `os.rmdir`, `os.rename`, `os.replace`, `os.chmod`, and `os.chown`
- `shutil` imports
- dynamic `eval` and `exec`
- direct access to sensitive absolute paths such as `/etc`, `/var`, `/usr`, `/bin`, `/sbin`, `/System`, `/Library`, and `~`
- selected `Path(...).write_text`, `write_bytes`, `unlink`, `rename`, `replace`, `chmod`, and `rmdir` calls

What is not claimed:

- this is not a hardened container, VM, seccomp profile, or OS-level sandbox
- pattern-based blocking cannot prove arbitrary untrusted Python is safe
- file reads/writes inside the temporary working directory remain possible
- the project does not claim protection against adversarial obfuscation

The honest security claim is: TraceFix is a lightweight course sandbox suitable for bounded demo/evaluation scripts, not for executing hostile code.

## Trust Concerns

The main trust concern is false-positive acceptance: a patch may remove the crash without preserving intended behavior.

TraceFix reduces that risk by:

- separating verification from patch generation
- using expected output when available
- escalating when behavior cannot be trusted automatically
- stopping when retries are exhausted or patch evidence is weak
- keeping the Verifier deterministic-first even when provider enhancement is enabled elsewhere

## Ambiguity Handling

When user intent or expected behavior is unclear, TraceFix should not pretend certainty.

Instead, it should:

- record uncertainty explicitly
- avoid broad speculative edits
- escalate rather than auto-accept

If API enhancement is enabled, ambiguity handling should still preserve those rules. Provider output may help produce better diagnoses or patches, but it must not override scope limits or acceptance boundaries.

This is especially important for cases where execution succeeds after patching but no reliable behavior oracle exists.

## Misuse Risks

Possible misuse or over-claim risks include:

- presenting the system as a general autonomous debugger
- assuming it can safely handle arbitrary user code
- using it for multi-file or internet-dependent projects outside scope
- over-trusting accepted patches without reviewing evidence
- presenting optional provider enhancement as if it removed the need for evidence or review

The documentation and evaluation package should make these limits explicit.

## Why TraceFix Does Not Install Packages, Access the Internet, or Debug Multi-File Systems

These exclusions are deliberate governance choices:

- package installation would widen scope and hide environmental assumptions
- internet access would reduce reproducibility and introduce uncontrolled dependencies
- multi-file debugging would require broader repository reasoning, dependency tracking, and higher-risk patching

By refusing those behaviors, TraceFix remains narrow, auditable, and aligned with its course-project goals.

## Why API Enhancement Is Optional and Local Inspectability Still Matters

TraceFix now supports optional provider-backed Diagnoser and Patcher behavior for better repair quality, but that enhancement is deliberately constrained:

- local mode remains the default
- provider-backed behavior is limited to single-file diagnosis and patch synthesis
- the Controller, Executor, Verifier, traces, state, and evaluation remain local
- provider failures fall back to local logic where configured
- traces record provider name, model name, fallback usage, and provider errors

This keeps the system course-appropriate. The project can still be run and evaluated without external services, while optional API mode can improve demos and repair quality when credentials are available.
