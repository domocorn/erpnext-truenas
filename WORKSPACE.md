# Workspace and folder guide

Windows workspace: `D:\Users\Dominic\Documents\_04 Tech & Coding\GitHub`.
This is a parent folder containing separate Git repositories, not a repository
to push as one unit. `polybar-configurator` and `.vscode` are unrelated to ERPNext.

| Folder | Purpose | GitHub handling |
| --- | --- | --- |
| `erpnext-truenas/` | Development tools, standalone generator, test procedures and evidence | Review and commit source/docs in this repository |
| `apps/` | TrueNAS catalog fork; final entry lives in `ix-dev/community/erpnext` | Review and commit catalog changes separately |
| `erpnext-truenas/catalog-dev/` | Catalog lifecycle tools, regression tests and runbooks | Source/docs belong in Git |
| `erpnext-truenas/catalog-dev/docs/tests/` | Completed VM test procedures | Historical evidence and reproducible procedures |
| `erpnext-truenas/catalog-dev/docs/reviews/` | Validation, image and lifecycle reviews | Source review evidence |
| `erpnext-truenas/catalog-dev/docs/submission/` | Publication preparation and local PR draft | Review before opening a PR |
| `erpnext-truenas/catalog-dev/docs/guides/` | Operational reference guides | Source documentation |
| `erpnext-truenas/catalog-dev/docs/history/` | Preserved superseded status documents | Historical reference, not current instructions |
| `erpnext-truenas/catalog-dev/assets/` | Proposed catalog artwork | Source asset; final icon metadata is pending |
| `erpnext-truenas/generated/` | Private standalone deployment YAML and recovery plans | Ignored; preserve locally, do not upload |
| `erpnext-truenas/catalog-dev/generated/` | Private rehearsal YAML and generated native test bundle | Ignored; preserve locally, do not upload wholesale |
| `.venv/`, `__pycache__/`, rendered output | Local dependencies or disposable generated files | Ignored; not contribution source |

The native lab archive contains code/metadata, but the generated folders also
contain other files with credentials. Their Git ignore protection remains in
place. Do not force-add generated files or backups.

## Current starting point

Follow [NEXT-STEPS.md](catalog-dev/NEXT-STEPS.md), then
[SUBMISSION-PREPARATION.md](catalog-dev/docs/submission/SUBMISSION-PREPARATION.md) for draft review.
The completed VM runbooks' PowerShell
commands assume the workspace above, so relative paths start with
`.\erpnext-truenas\`. Commands run inside a repository must use that repository's
own directory instead.

`apps/ix-dev/community/erpnext` is the default catalog draft and now contains the
tested normal native hooks. The development builder adds failure/recovery
fixtures only to separate generated lab candidates.

## Before either repository is pushed

Review each repository's diff and staged files separately. Include source,
tests, runbooks and documented evidence; exclude credentials, generated Compose
files, site configuration, database exports and recovery archives. Preserve
historical recovery material until the native failure/recovery tests finish.
Do not rearrange lifecycle Python modules just for appearance: the generators,
embedded scripts and tests import those modules by their current paths.

Cleanup on 2026-10-26 leaves only README, NEXT-STEPS and HANDOFF documents at the
catalog-dev root. Runbooks, reviews, submission notes, guides and history are
grouped under docs/. Builders retain the original runbook filenames in deployed
bundles. Source, virtual environments, generated deployments and backups are
preserved; private artifacts remain ignored. Both working branches are
erpnext-catalog-draft and commits/pushes are authorized. Opening a PR remains
a separate action.
