# Security Policy

This file describes how to report a vulnerability in DSIS. It is separate from
the [security audit history](docs/SECURITY_AUDIT_REPORT.md) and remediation
record (see [the documentation index](docs/INDEX.md)).

## Supported Versions

The repository currently identifies its release line as `v0.1.0`. Security
fixes are considered for the current `v0.1.x` line.

| Version | Supported |
| --- | --- |
| `v0.1.x` | Yes |
| Older or unversioned snapshots | No commitment |

## Reporting a Vulnerability

Email vulnerability reports to [jaydendollaga4@gmail.com](mailto:jaydendollaga4@gmail.com). This address is
also the maintainer address recorded in the repository's community files and
Git history.

Please include:

- A short description of the issue and its impact
- The affected version or commit
- Reproduction steps or a proof of concept, if safe to share
- Any suggested mitigation

Please do not disclose an unresolved vulnerability publicly before the project
maintainer has had an opportunity to assess it.

## Response Expectations

We aim to acknowledge a report within 3 business days and provide an initial
assessment or status update within 7 business days. Timing may vary for reports
requiring hardware reproduction or third-party coordination.

Accepted reports will be tracked to a fix or mitigation when practical. Reports
that are declined will receive an explanation when the available information
allows a clear determination.

## Scope Notes

DSIS may process student and attendance data locally. Do not include real
student records, fingerprint data, database files, or private logs in a report;
use redacted examples instead.

See [LICENSE](LICENSE) for the project's software license.
