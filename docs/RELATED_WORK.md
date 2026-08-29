# Related work and name check

Checked on 2026-08-29 against primary project pages, repositories, papers, and
GitHub search. Fleet Failure Atlas is intentionally narrower than an incident
database and different from an agent capability benchmark: it publishes small,
safe, executable reliability mechanisms for coding-agent orchestration.

## Adjacent work

- [SWE-bench](https://github.com/SWE-bench/SWE-bench) evaluates whether a model
  can resolve real software issues in reproducible environments. It measures
  task outcomes; this atlas focuses on operational failure mechanisms around
  agent work, evidence, coordination, and regression defense.
- [Understanding Software Engineering Agents](https://arxiv.org/abs/2506.18824)
  studies thought-action-result trajectories and identifies behavioral motifs
  and anti-patterns. The atlas complements trajectory research with tiny
  executable fixtures intended for local engineering regression checks.
- The [AI Incident Database](https://incidentdatabase.ai/about/) catalogs public
  reports of AI harms and incidents. The atlas is not an incident registry: a
  hypothetical mechanism is welcome when it is clearly labelled and safely
  reproducible, while unsupported incident attribution is not.
- [MITRE ATLAS](https://atlas.mitre.org/) is a knowledge base for adversarial
  threats to AI-enabled systems. Fleet Failure Atlas addresses non-adversarial
  reliability failures in autonomous coding-agent systems and is not a threat
  framework.
- GitHub's [Checks API](https://docs.github.com/en/rest/checks/runs) exposes the
  exact `head_sha` associated with a check run. FFA-001 uses a platform-neutral
  synthetic receipt to demonstrate why that identity must be bound to a merge
  candidate.

## Name verification

On 2026-08-29, an exact GitHub repository-name search for `fleet failure atlas`
returned only this repository. General web and GitHub searches found projects
using the generic word “atlas” (including MITRE ATLAS), but no software project
with the exact name “Fleet Failure Atlas.” This is a collision check, not a
trademark opinion or guarantee. Recheck before any future rebrand or package
registration.

## Citation policy

Link to the primary source when possible. State what it actually supports,
separate inference from reported fact, and quote only what is needed. External
reports never replace the atlas requirement for a safe fixture and deterministic
detector.
