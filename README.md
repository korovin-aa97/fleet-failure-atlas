# Fleet Failure Atlas

Private draft of an executable field guide to failures in autonomous coding
agent fleets.

The project is meant to be more than a list of stories. Each published pattern
should eventually contain:

1. a minimal fixture that reproduces the failure;
2. an observable signature;
3. a deterministic detector;
4. a regression check for the repair;
5. the boundary where a human must intervene.

This initial extraction contains a generic regression-review checklist and a
small set of sanitized patterns. Product names, hosts, branch names, customer
data, and private fleet topology have deliberately been removed.

## Candidate first release

- regression review checklist;
- green-CI/stale-evidence failure;
- background-worker artifact deadlock;
- concurrent queue update loss;
- timezone-dependent test failure.

The fixtures and detectors are still TODO. This draft has not been tested.

No public license has been selected while this repository is private.
