> Catalog PR architecture changed after review: see [thin integration review](catalog-dev/docs/reviews/THIN-INTEGRATION-REVIEW.md). Older guarded lifecycle instructions apply only to the archive branch, not the current submission. Production is unchanged.

# ERPNext for TrueNAS

Community development project. Not an official Frappe, TrueNAS, or HexOS product.

## Current catalog work

Native catalog installation, upgrade, migration-failure blocking, independent
recovery and restart passed by user report. The tested normal lifecycle is now
integrated into the catalog draft. Draft review preparation is complete; the
approved CDN icon URL and full metadata validation remain pending.
Start with [current next steps](catalog-dev/NEXT-STEPS.md). See the
[workspace and folder guide](WORKSPACE.md) before committing or pushing.
The catalog candidate has not been submitted or accepted by TrueNAS.

## Standalone first-install lab generator

This repository generates a standalone Compose YAML for a **new test installation**
on TrueNAS 25.10.7. It includes MariaDB, Redis, Frappe configuration, automatic
ERPNext site creation, workers, scheduler, websocket, and the web frontend.

**Not published in Discover or curated for HexOS. This standalone generator does
not implement the catalog lifecycle described above or import existing sites.
Do not use this prototype for business data.**

The generated YAML embeds the initializer, so TrueNAS does not need the repository
files mounted into the app. It uses project-scoped Docker volumes, without fixed
production paths or container names. Only the frontend publishes a host port.

## Windows quick start

Open PowerShell in the repository folder. Install Python 3 if `py` is unavailable.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/build.py
```

Choose a test administrator password when prompted. The generator makes a random
database root password and stores it in the generated YAML. Do not share that YAML
or add it to Git. The generated directory is ignored by Git.

Follow [the VM lab guide](docs/LAB.md). Project source can be public. Generated
configuration and backups must stay private.

## Development boundaries

- amd64 lab target; ERPNext v16.51.1; MariaDB 11.8; Redis 8.6-alpine.
- Image availability and real container behavior require testing on the VM.
- No public TLS or bundled reverse proxy. HTTP is for the isolated lab.
- Initializer validates a project-created site on rerun and refuses unmanaged or
  interrupted installations. It never automatically deletes or resets a site.
- Credentials are visible to the TrueNAS administrator in app configuration and
  container inspection. The installation command supplies credentials to Bench.
- A changed initial administrator password does not reset an existing account.
- No upgrade automation: do not change image versions to test updates yet.

See [the roadmap](docs/ROADMAP.md) for catalog and HexOS work.

## Upstream references

- https://github.com/frappe/frappe_docker
- https://github.com/truenas/apps/blob/master/CONTRIBUTIONS.md
- https://docs.hexos.com/features/apps/install-scripts/

The upstream official image supplies ERPNext/Frappe; their licenses apply to that
software. Review repository licensing before public contributions. No production
credentials or configuration from the author's live installation are included.

## Backup and restore lab

Follow [the restore acceptance test](docs/RESTORE-TEST.md) after the initial
installation tests pass. This manual lab procedure does not provide automated
upgrade or restore support.

## Controlled upgrade rehearsal

A staged lab-only upgrade generator is now available. It reads the exact installed
private YAML and preserves credentials, volumes, infrastructure versions and web
port. Follow [UPGRADE-TEST.md](docs/UPGRADE-TEST.md). This is not yet one-click
updating or a validated real version transition. Do not run it on business data.

## Real patch-version upgrade test

The installer generator accepts `--erpnext-version v16.51.0` for a fresh test
installation. It refuses to overwrite an existing generated file. Follow
[REAL-UPGRADE-TEST.md](docs/REAL-UPGRADE-TEST.md) for the isolated v16.51.0 to
v16.51.1 test, with distinct numbered stages and explicit shutdown commands.
Existing rehearsal filenames remain available for backwards compatibility.
