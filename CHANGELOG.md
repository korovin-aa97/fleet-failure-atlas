# Changelog

All notable changes are documented here. The project follows
[Semantic Versioning](https://semver.org/) for runner and schema compatibility;
published pattern IDs remain stable.

## [0.1.2] - 2026-08-30

### Fixed

- tolerate the macOS process-exit race where `killpg()` reports `EPERM` after
  the bounded fixture has already finished;
- fall back to terminating the owned child directly when the process remains
  alive after a process-group permission error.

### Changed

- the README and repository social artwork now explain the nontechnical flow
  from failure pattern through reproduction and detection to a regression guard.

## [0.1.1] - 2026-08-30

### Fixed

- lifecycle filtering now matches every declared stage, and search covers
  stable IDs, status, and provenance;
- filter results are announced accessibly and include a clear empty state;
- the stale-CI regression proves both stale rejection and fresh acceptance;
- malformed, oversized, non-UTF-8, timed-out, and path-escaping fixtures now
  fail closed with bounded diagnostics.

### Changed

- documented-only entries now have an explicit `fixture: none` contract;
- fixture checks no longer rely on Python assertions and run without `PATH`;
- CI adds pinned lint, formatting, strict typing, security analysis, Python
  3.14, and a Windows smoke lane; workflow actions are commit-pinned;
- local-link and publication safety scans cover the full publishable tree.

## [0.1.0] - 2026-08-29

### Added

- four clean-room executable patterns spanning evidence, orchestration,
  coordination, and time handling;
- bounded standard-library fixture runner with reproduce, detect, and regression
  modes;
- pattern/schema, local-link, safety, and skill-alignment validation;
- searchable static atlas and machine-readable JSON index;
- generic regression-review agent skill and human checklist;
- contribution, provenance, security, governance, and CI/release foundations.
