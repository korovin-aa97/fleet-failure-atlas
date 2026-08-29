# Security policy

## Supported versions

Security fixes are applied to the latest release and `main`.

## Report privately

Use GitHub's **Report a vulnerability** form in the repository Security tab.
Please include the affected pattern or runner behavior, impact, minimal safe
reproduction, and suggested mitigation. Do not place credentials, private data,
or weaponized reproductions in a public issue.

Maintainers aim to acknowledge a report within 72 hours and provide a triage
decision within seven days. Timelines may change with severity and maintainer
availability.

## Scope

Reports about the runner escaping its temporary directory, unintended network or
credential access, unsafe fixture behavior, secret disclosure, generated-site
injection, or dependency/workflow compromise are in scope. Generic prompt
injection claims without an executable impact on this repository are not.

The fixture runner is a containment aid, not a security sandbox. Review code
before running fixtures from an untrusted branch.
