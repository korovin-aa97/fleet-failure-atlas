# Regression review checklist

Use this after checking whether a change satisfies its stated goal. The purpose
is to catch damage outside the line of code that was intentionally changed.

## Contract walk

For every changed public function or command:

- find every caller from the merge base;
- confirm the return type is unchanged;
- confirm parameters, defaults, exceptions, side effects, and logging contracts
  remain compatible;
- distinguish the merge-base diff from unrelated changes that landed later;
- verify suspicious branch diffs with a merge simulation before reporting a
  deletion or regression.

## Common regression smells

### Public API

- a public method was removed or renamed;
- a required parameter was added;
- parameter order changed for positional callers;
- a list became an iterator, a mapping became a tuple, or sync became async;
- accepted inputs were narrowed without updating callers.

### Defaults and configuration

- a default value or flag behaviour changed silently;
- a runtime setting became a hard-coded constant;
- a new environment variable has no safe default or documentation.

### Error and observability contracts

- an exception handler was removed or narrowed;
- a previously handled failure now escapes;
- a log message, severity, or structured field used by monitoring changed;
- a retry, timeout, lock, or semaphore was removed without proving the original
  failure mode is gone.

### Data contracts

- code reads a field that may not exist in the deployed schema;
- an upsert key or freshness field changed;
- a migration is missing, irreversible, or incompatible with existing data;
- a mutation no longer leaves an audit trail.

### Test integrity

- existing assertions were deleted or replaced with mocks of the final value;
- a previously passing test is now skipped;
- tests cover the helper but not the public behaviour;
- a green result is stale, belongs to another commit, or did not cover the
  changed surface.

## Review evidence

Record the exact commit, changed surface, checks independently rerun, callers
inspected, and any unverified assumptions. Do not treat the implementer's own
summary as independent evidence.
