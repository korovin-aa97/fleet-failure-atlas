---
name: regression-review
description: Review a proposed code change for regressions outside its stated goal, including public API, configuration, errors, observability, data contracts, and test integrity.
---

# Regression review

## When to use

Use after correctness review and before approving or merging a code change. Read
the repository's local instructions first. Inspect the merge-base diff, relevant
callers, tests, and CI evidence; do not trust a change author's summary as
independent proof.

<!-- checklist:start -->
## Contract walk

For every changed public function, command, schema, or event:

- find callers and consumers from the merge base;
- confirm return types, parameters, defaults, exceptions, side effects, and
  observability remain compatible;
- distinguish the proposed diff from unrelated changes that landed later;
- verify suspicious branch diffs with a merge simulation before reporting a
  deletion or regression.

## Public API and configuration

- flag removed or renamed public methods and commands;
- flag new required parameters, reordered positional parameters, narrowed
  accepted inputs, or sync/async changes;
- flag silent default or flag-behavior changes;
- require safe defaults and documentation for new environment variables;
- reject runtime settings silently replaced with hard-coded constants.

## Errors and observability

- inspect removed or narrowed exception handlers;
- preserve documented retries, timeouts, locks, and semaphores until their
  original failure invariant is demonstrably obsolete;
- treat log severity and structured fields consumed by monitors as interfaces;
- ensure a newly escaping failure has an intentional caller contract.

## Data contracts

- verify code tolerates the deployed schema during rollout;
- inspect changed upsert, identity, ordering, and freshness keys;
- require forward-compatible migrations and a rollback or recovery statement;
- preserve audit evidence for consequential mutations.

## Test integrity

- reject deleted assertions disguised as simplification;
- flag newly skipped tests and mocks of the final value;
- test public behavior, not only the helper introduced by the change;
- bind green evidence to the exact revision and changed surface;
- record the exact commit, checks independently rerun, callers inspected, and
  all remaining assumptions.
<!-- checklist:end -->

## Output contract

Return either `APPROVED` or a short list of actionable findings. Each finding
must identify the affected contract, concrete caller or scenario, evidence, and
smallest credible repair. Label hypotheses. Do not report style preferences as
regressions.
