# Safety and provenance model

The atlas must be safe to clone and run on an ordinary developer machine.

## Fixture containment

The runner starts each fixture as a subprocess in a new temporary directory,
passes only an allowlist of non-secret runtime variables (and no `PATH`),
enforces a five-second deadline and a 64 KiB ceiling per output stream,
terminates its process group on POSIX, and removes the directory afterward.
Fixtures use synthetic data and the Python standard library. These controls
reduce accidental impact; code review remains mandatory because a subprocess
is not a security sandbox.

## Rejected content

Maintainers reject fixtures that require production access, credentials,
network mutation, destructive host actions, uncontrolled compute or storage,
privilege escalation, persistence, evasion, or private topology. A useful but
unsafe mechanism should be described at a defensive level or omitted.

## Sanitization review

Before release, search current content and history for organization and customer
names, hostnames, user paths, branch names, incident identifiers, tokens, private
URLs, and architecture that is not necessary to understand the invariant. The
built-in safety scan catches a small deny-list and common secret formats; it is
not a substitute for human review or a dedicated secret scanner.

## Evidence language

Every entry declares one provenance category defined in
[the schema](PATTERN_SCHEMA.md). Avoid causal or frequency claims that the
fixture cannot prove. Use “the fixture demonstrates” for synthetic evidence and
reserve “the incident showed” for a cited public incident.

## Reporting a safety concern

Do not open a public issue containing an exploit, credential, personal data, or
private infrastructure detail. Follow [the security policy](../SECURITY.md).
