# ERPNext for TrueNAS

Community development project. Not an official Frappe, TrueNAS, or HexOS product.

## Status: first-install lab prototype

This repository generates a standalone Compose YAML for a **new test installation**
on TrueNAS 25.10.7. It includes MariaDB, Redis, Frappe configuration, automatic
ERPNext site creation, workers, scheduler, websocket, and the web frontend.

**Not yet a Discover catalog app or HexOS curation. Automated upgrades and existing
site import are not implemented. Do not use this prototype for business data.**

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
