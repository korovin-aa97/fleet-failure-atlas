# Stale green CI evidence

## Symptom

A change is merged because all required checks appear green, but the checks
belong to an older commit or did not include the changed surface.

## Mechanism

The reviewer treats a check name as proof without binding it to the exact head
commit, coverage declaration, and immutable policy that selected the checks.

## Observable signature

- check completion SHA differs from the merge candidate SHA;
- policy or workflow files changed in the same proposal they judge;
- a required job exists but internally skipped every relevant command;
- generated evidence predates the final source change.

## Generic defense

Require an exact-SHA receipt, immutable verifier policy, and an explicit
changed-surface-to-check mapping. Fail closed when any element is missing.

## Fixture TODO

Create a two-commit pull request where the first commit is green and the second
changes source without regenerating evidence.
