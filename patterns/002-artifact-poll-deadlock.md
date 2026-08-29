# Background worker artifact deadlock

## Symptom

An orchestrator starts a worker in the background and waits until timeout for a
file that the worker never promised to create.

## Mechanism

The worker returns its result through the orchestration protocol, while the
parent polls a guessed filesystem path. Both sides can be healthy and the run
still never completes.

## Observable signature

- a long-running polling loop on a fixed artifact path;
- the worker has already returned a valid inline result;
- the parent remains active until its global timeout;
- downstream work accumulates despite available compute.

## Generic defense

Use one explicit result channel. Consume the returned result directly, or
define and validate a durable artifact contract before starting the worker.
Missing or malformed results should fail once, not trigger an unbounded poll.

## Fixture TODO

Provide a worker that returns JSON to stdout while the parent incorrectly polls
for `result.json`.
