# Documentation Manifest

This manifest records the reorganized documentation surface at the current repository snapshot. Existing historical files retain their paths so links and audit references remain stable; the section `README.md` files are the navigational entry points.

## Canonical operational documentation

- `README.md` — public project overview and quick start.
- `INSTALLATION.md` — root installation entry point.
- `PORTABLE_BUILD.md` — packaged/portable build guidance.
- `RELEASE.md` — release readiness and validation boundary.
- `CONTRIBUTING.md` — contributor workflow and checks.
- `SECURITY.md` — security policy and disclosure boundary.
- `docs/README.md`, `docs/INDEX.md` — documentation landing pages.
- `docs/UserGuide/README.md`, `installation-guide.md`, `project-overview.md`, `v3-workflows.md`, `testing-results.md` — user and operator guidance.
- `docs/Architecture/README.md`, `v3-system.md`, `runtime-contract.md`, `software-flow.md`, `database-schema.md`, `system-architecture.md` — v3 architecture and data contracts.
- `docs/Hardware/README.md`, `hardware-connections.md`, `wiring.md`, `firmware-variants.md`, `serial-protocol.md` — physical and firmware guidance.
- `docs/Development/README.md`, `documentation-authority.md`, `documentation-manifest.md`, `FILES_OVERVIEW.md`, `FILES_DETAILED.md`, `logging-guide.md`, `runtime-data.md`, `database-updates.md`, `tools-catalog.md` — developer reference.
- `docs/API/README.md` — frontend/Python bridge reference.
- `docs/Troubleshooting/README.md` — current recovery guide.

## Historical, generated, or research material

- `docs/History/` — version lineage and migration context.
- `docs/generated/` — generated snapshots; verify against source before use.
- `docs/Research/` — concept and study material.
- `docs/Dup/` — duplicate or superseded material retained for provenance.
- `docs/*AUDIT*.md`, `docs/*DIAGNOSTIC*.md`, and `docs/*ROOT_CAUSE*.md` — incident or forensic records scoped to their stated snapshot.
- `archive/` and `python/gui_web/v2_reference/` — legacy and reference implementation documentation.
- `tests/_reference/` — historical test operator notes; current commands belong in contributor/development guides.

## Maintenance rule

A new current behavior should be documented in exactly one canonical guide and linked from the relevant section README. Historical reports may link back to that guide, but should retain their original conclusions and scope. Before release, validate Markdown paths, source references, and the documentation tree against the current commit.
