> Current architecture: [thin upstream integration](docs/reviews/THIN-INTEGRATION-REVIEW.md), replacing the guarded framework after maintainer feedback. Manual site setup/operations; no app-internal scripts shipped. Old acceptance results are historical and do not validate this rewrite. Runtime tests pending because the VM is unreachable and WSL cannot start.

# Catalog development

This directory contains the ERPNext catalog development tools and evidence. The
actual TrueNAS contribution is in the separate `apps/ix-dev/community/erpnext`
checkout. Do not submit this development directory to the TrueNAS catalog repo.

The planned native lifecycle VM tests are complete. Start with
[NEXT-STEPS.md](NEXT-STEPS.md) for current status or [HANDOFF.md](HANDOFF.md) when
continuing development in a new session. No additional VM rehearsal is requested.

## Documentation

| Topic | Read |
| --- | --- |
| Publication status and remaining icon item | [Submission preparation](docs/submission/SUBMISSION-PREPARATION.md) |
| Local, unposted PR description | [Review draft](docs/submission/REVIEW-DRAFT.md) |
| Validation evidence and limits | [Validation record](docs/reviews/VALIDATION.md) |
| Upgrade design and exclusion | [Lifecycle review](docs/reviews/LIFECYCLE-REVIEW.md) |
| Image references and digests | [Image review](docs/reviews/IMAGE-REVIEW.md) |
| Native integration history | [Native progress](docs/reviews/NATIVE-CATALOG-PROGRESS.md) |
| Completed native install/upgrade procedure | [Native catalog test](docs/tests/NATIVE-CATALOG-TEST.md) |
| Completed failed-upgrade and restore procedure | [Native failure/recovery test](docs/tests/NATIVE-FAILURE-RECOVERY-TEST.md) |
| Private backup transfer procedure | [Recovery copy guide](docs/guides/RECOVERY-COPY.md) |
| Wider project test record | [Test results](../docs/TEST-RESULTS.md) |

Older runbooks are under [docs/tests/](docs/tests/). Superseded status snapshots
and the original first-install guide are under [docs/history/](docs/history/).
They are historical evidence, not instructions to repeat completed VM testing.

## Folder layout

- Root: the three entry-point documents, Python tools/tests and requirements.
- `docs/tests/`: VM test procedures.
- `docs/reviews/`: validation and lifecycle/image investigations.
- `docs/submission/`: contribution preparation and draft description.
- `docs/guides/`: operational reference material.
- `docs/history/`: preserved superseded instructions.
- `assets/`: proposed catalog artwork and its provenance.
- `generated/`, `.venv/`, Python caches: private or disposable output, ignored by Git.

Source, tests, documentation and artwork belong in this development repository.
Generated deployment YAML and recovery material can contain credentials and must
stay private. Keep Python modules at their current paths because the generators
and embedded scripts import them. The bundle builders read runbooks from
`docs/tests/` and keep their original filenames inside generated transfer bundles.
