# Concurrent queue update loss

## Symptom

One worker closes an item while another appends a new item, and the new item
silently disappears.

## Mechanism

Both workers edit snapshots of the same queue. A merge strategy chooses an
entire file from one side instead of replaying the two logical operations.

## Observable signature

- two successful commits touch the queue close together;
- repository history is clean but one stable item ID is absent;
- the merge used whole-file conflict resolution;
- producer logs prove the missing append was accepted before the merge.

## Generic defense

Represent updates as stable-key operations. Apply the exact removal or append
to the latest remote state and use a non-force compare-and-swap push. On
rejection, reload the new state and replay the operation.

## Fixture TODO

Create two processes that remove and append against the same initial YAML file.
