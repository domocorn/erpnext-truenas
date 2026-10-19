# Local Codex handoff — ERPNext for TrueNAS

Open both local repositories in a VS Code workspace: `erpnext-truenas` and `apps`.
Read each repository's AGENTS.md if present and apps/CONTRIBUTIONS.md before changes.

User: domocorn. GitHub project https://github.com/domocorn/erpnext-truenas.
User forked/cloned truenas/apps. TrueNAS test target 25.10.7 in VMware Workstation
on Windows with 32 GB RAM; VM allocated ~12 GB RAM. Production NAS exists and MUST
remain untouched. Testing uses fictional business data in a disposable VM.

## Already tested by the user

Standalone Compose generator automatically installs ERPNext with official images.
Initialization, app/VM restart, unchanged configuration save, multiple isolated
instances, database/public-private file restore, simulated pre-migration failure,
guarded startup, same-version migration and real ERPNext 16.51.0→16.51.1 patch
upgrade passed. Frappe was 16.52.0 before/after that patch. Results are user-reported;
see docs/TEST-RESULTS.md. Encrypted credential decryption and recovery from an actual
mid-patch database failure remain untested. No general major-upgrade claim.

## Existing development

scripts/build.py generates private YAML, supports --erpnext-version, defaults to
v16.51.1, and refuses output overwrite. scripts/prepare_upgrade.py reads the EXACT
installed private YAML, preserving secrets/storage and generating offline backup,
simulated failure, guarded resume and migration stages. --numbered-stages gives
unique 01–05 filenames. Operation IDs and persisted .nas-upgrade-state.json prevent
blind repeats. New operation plans must use the previous successful resume YAML.
Never regenerate build.py output to modify an existing deployment's database password.

## Current milestone

New catalog draft under apps/ix-dev/community/erpnext, local render tools under
erpnext-truenas/catalog-dev. Uses native TrueNAS library 2.3.17. Form schema,
metadata, image values, permissions, MariaDB dependency, port and portal metadata.
Dataset-backed mounts require bootstrap of Frappe assets from image sites directory;
bootstrap runs before mounting the real sites path into initializer/runtime.

This catalog draft is FRESH INSTALL ONLY and version-locked: bootstrap blocks image
tag changes. It is not catalog accepted, not update-ready and not HexOS curated.
Do not transfer the prototype's upgrade promises to it without reengineering and
retesting the different mount/permissions/deployment lifecycle.

## Next work

1. Read catalog-dev/README.md. Run local render checks, then user tests rendered
   YAML as NEW erpnext-catalog-test on port 18084 with dedicated lab directories.
2. Complete official middleware/schema/Docker catalog validation, official library
   vendoring and metadata generation, icon and image policy review, worker healthchecks.
3. Integrate safe catalog upgrades (stop/drain old workers, backup, migration gate,
   new runtime). Prevent false claims about automatic rollback after DB patches.
4. Check existing issues/PRs before a reviewed community-train submission.
5. Later build a thin HexOS curation wrapper; community submissions are supported,
   but official inclusion requires HexOS review. Verify current scripts/docs first.

Keep generated YAML/passwords/site configs/backups private. Never stage .venv,
generated/ or private data. User uses GitHub Desktop; explain which repository and
branch receives each change. Do not push, submit PRs, or post messages without
explicit user instructions. Provide meaningful tests and clear evidence limits.
