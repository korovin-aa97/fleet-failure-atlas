# Release inventory and clean-room classification

Reviewed: 2026-09-10. This inventory records what was considered for the
published collection and why it is safe to publish. It intentionally contains
no private system names, paths, identities, incidents, or topology.

| Candidate | Classification | Release decision | Sanitization/evidence decision |
| --- | --- | --- | --- |
| Stale green CI evidence | Public after abstraction | `FFA-001` | Synthetic SHAs and receipts; no repository or real check history. |
| Result-channel mismatch | Public after abstraction | `FFA-002` | In-memory result and bounded path checks; no orchestrator protocol details. |
| Concurrent queue update loss | Public after abstraction | `FFA-003` | In-memory stable-key operations; no real queue, branch, or storage topology. |
| Timezone-dependent test | Public as-is | `FFA-004` | Constructed instant and public IANA timezone only. |
| Fresh review, stale citation | Public external report plus abstraction | `FFA-005` | Cite the public report/PR; reproduce only with synthetic text, SHAs, anchors, and ranges. |
| Private operational incidents | Internal-only | Excluded | No incident narrative or identifiers were imported. |
| Orchestrator implementation details | Commercial know-how | Excluded | Only the generic result-channel invariant is documented. |

## Claim audit

All four v0.1.0 entries are labelled `hypothetical`. FFA-005 is labelled
`externally-reported` because its occurrence is supported by a public discussion
and pull request. Its fixture remains a clean-room synthetic mechanism and does
not attribute frequency, impact, or internal cause to the named service. The
related-work page explains adjacent public projects without claiming they
endorse this atlas.

## Publication boundary

Future contributors must start from a minimal synthetic mechanism. If an entry
originates in a private environment, replace names and data, remove unnecessary
architectural detail, and ensure the fixture independently proves the remaining
claim. A story that cannot cross that boundary stays out of the public atlas.
