> Subsequent automated testing is recorded in [UPDATE-16.52.1-AUTOMATED-TESTS.md](UPDATE-16.52.1-AUTOMATED-TESTS.md). The initial deferred-test and no-VM-operation statements below describe the groundwork commit only.

# ERPNext 16.52.1 update groundwork - 2026-10-28

Local-only branches in both repositories: `erpnext-catalog-update-16.52.1`.
The apps baseline is submitted PR head `780242c12c86132705f69602c165b758aab80ce4`;
the development baseline is `1c5f9d7`. Submitted branches and PR #6267 are unchanged.
Do not push or deploy this candidate before the deferred acceptance tests.

## Verified image identity

- Source: submitted ERPNext 16.51.1 index `sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268`.
- Source linux/amd64 config ID remains `sha256:0ce48f9b465e15869540282c8f203bdbe24b2ae9fe5419c2f32c7e462fba5591`.
- Target: `frappe/erpnext:v16.52.1@sha256:bc21532268c35cec5756c44a11fe510bfccbf23fb4ad651a38644d0c25b56299`.
- Target amd64 manifest: `sha256:9a03de369856870670b4f61fd81e5e977d8faccd4b8fa14a5dcfaed36513ea0e`.
- Target amd64 config: `sha256:034a4a45ea98c8a53f1f8aa1bf380e8103710f92cb0ade4011ea9e2c51ebaa34`.
- Registry build provenance sets ERPNEXT_BRANCH=v16.52.1 and FRAPPE_BRANCH=v16.53.0.
  This is the bundled Frappe version, not the separately latest Frappe 16.54.0.
- Provenance descriptor: `sha256:603e36fc32b3e3e64489eb451bd0bb3bca865ede76d96e3b2ff64e3cb55d33b4`.
  Published BuildKit/SLSA provenance was inspected; no independent signature verification is claimed.
- Build source: https://github.com/frappe/frappe_docker/commit/ef97dd8b393a32191a403f1a11a51c19b6c70ac2 .
  Config reports Python 3.14.10; provenance uses Python 3.14, Node 24, Debian trixie.
  Runtime compatibility remains untested. The index also lists arm64; only amd64
  metadata was investigated, with no runtime architecture claims.

Windows Python TLS validation failed due to an expired certificate; registry
inspection succeeded using Windows curl with normal certificate verification.
No TLS verification was disabled. No image was run or pulled through Docker.

## Candidate changes and release review

Catalog package 1.1.0 targets ERPNext 16.52.1. Only the exact pinned source-to-target
pair is permitted; older source sites are intentionally refused. Canonical policy,
generated inline scripts, lab builder app versions, mock fixtures and notes agree.
Lab package versions remain 0.9.0/source and 1.0.0/target to preserve the existing
lab staging/recovery protocol; they are distinct from real package versions.
MariaDB, Redis, permission utility, storage and runtime guards remain unchanged.

Reviewed upstream notes (not an exhaustive migration-code audit):
- https://github.com/frappe/erpnext/releases/tag/v16.51.2
- https://github.com/frappe/erpnext/releases/tag/v16.52.0
- https://github.com/frappe/erpnext/releases/tag/v16.52.1
- https://github.com/frappe/frappe/releases/tag/v16.53.0

ERPNext 16.52.0 includes manufacturing workflow and reporting changes; 16.52.1
changes moving-average valuation for reposted purchase returns. Frappe 16.53.0
includes database schema handling, private-file permissions and cache changes.
These require real migration/data/asset checks, not just version substitution.

## Local validation and next session

Passed Linux suites: patch 11, native lifecycle 9, queue guard 9, native catalog
staging 4, native failure staging 9, native restore 3, recovery input 3, catalog
rendering 11 (counts include inherited cases). These use mocks/local temporary
files and are not Docker integration or TrueNAS execution.

Deferred: Docker fresh install and 16.51.1-to-16.52.1 migration; then disposable
TrueNAS native install/upgrade, record/private attachment and encrypted-value
preservation, all referenced CSS/JS returning correct content types, unchanged
restart without another migration/backup, deliberate migration failure blocking
and independent source-image recovery. Never reuse or modify the old VM lab
state blindly; prepare new isolated bundles/storage when testing resumes.

Full official metadata/CI remains pending the approved icon URL and later full
validation. No production connection, VM operation, push, PR update, dependency
upgrade or backup cleanup was performed. Production success does not validate
this catalog digest or lifecycle.
