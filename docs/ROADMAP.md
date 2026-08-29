# Roadmap

Fleet Failure Atlas grows by evidence quality, not entry count.

## Next

- collect independent clean-clone results across Linux, macOS, and Windows;
- improve accessibility and keyboard behavior of the static filter;
- add a schema migration policy before metadata needs to change;
- accept new executable patterns only when they contribute a distinct detector
  and regression invariant.

## Candidate patterns

Candidates are deliberately not pre-labelled as incidents:

- a task reports completion before its durable side effect is observable;
- retry logic duplicates a non-idempotent side effect;
- a reviewer validates the patch but not the deployed migration order;
- context truncation silently drops an authority or safety instruction.

Each needs a safe clean-room fixture and must clear the same provenance and
false-positive bar as the first collection.

## Not planned

The project will not become an agent framework, hosted telemetry service,
vendor leaderboard, private incident dump, or collection of unsafe chaos
scripts. If external contributions do not justify active expansion, the atlas
will remain a small maintained reference.
