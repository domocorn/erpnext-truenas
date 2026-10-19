# ERPNext catalog draft: first rendered deployment

This directory belongs in **erpnext-truenas**. The separate package directory
`ix-dev/community/erpnext` belongs in your **apps** fork. Do not submit catalog-dev
as part of a truenas/apps contribution.

## What is new

A real `questions.yaml` defines the installation form. A Jinja template uses
TrueNAS's actual library 2.3.17, storage/perms helper, MariaDB dependency, port
handling, and portal metadata. This draft is not accepted into Discover and has
not been run through official middleware or Docker-based catalog CI. The icon,
library vendoring/hash, metadata generation, worker health probes and catalog
upgrade coordination remain pre-submission work.

Installing rendered YAML exercises the deployment and permission changes; it
DOES NOT test the form inside TrueNAS or guarantee a portal button in custom-app
mode. The x-portals metadata is for the eventual catalog integration.

The tested standalone prototype and the new catalog storage layout are separate.
Do not point this draft at existing prototype storage. No catalog image upgrades
or import are supported yet. The bootstrap refuses a changed image tag before
initialization. Staged prototype upgrades do not automatically apply to this layout.

## 1. Copy files to the correct repositories

The ZIP has two top-level folders:

- `apps/ix-dev/community/erpnext/` → your apps repository's `ix-dev/community/erpnext/`.
- `erpnext-truenas/catalog-dev/` → your erpnext-truenas repository's `catalog-dev/`.

Do not create another nested apps/apps or erpnext-truenas/erpnext-truenas folder.
Create a development branch in your apps fork before copying. Keep the existing
production/test applications unchanged. Latest upstream apps library at authoring
was 2.3.17; if your clone lacks `library/2.3.17`, sync the fork with upstream first.

## 2. Render on Windows

Open PowerShell in the **erpnext-truenas** repository. These examples assume the
apps checkout is in its sibling directory `..\apps`. Replace that path if needed.
No Docker engine or WSL is required for this LOCAL preview. Python Docker SDK is
only a library dependency and its unavailable daemon is handled off TrueNAS.

```powershell
py -3 -m venv catalog-dev/.venv
.\catalog-dev\.venv\Scripts\python.exe -m pip install -r catalog-dev/requirements.txt
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/test_catalog.py --apps-root ..\apps -v
.\catalog-dev\.venv\Scripts\python.exe catalog-dev/render_catalog.py --apps-root ..\apps --lab-root /mnt/labpool/erpnext-catalog-test --port 18084
```

If `py -3` reports no installed Python but `python --version` works, use
`python -m venv catalog-dev/.venv` for the first command instead.

Choose new test administrator and database passwords. Generated output:
`catalog-dev/generated/catalog-test.yaml`. It contains secrets and is gitignored.
Keep it privately; do not regenerate to update an initialized database password.
Four local tests pass on Linux. On Windows the two tests that execute Linux
bootstrap/locking are skipped; the two library rendering tests still run.

If imports or rendering fail on your machine, send the error before deploying.
Windows rendering was not executed in the authoring Linux environment.

## 3. Prepare dedicated directories in the test VM

Take a VM snapshot. In the VM's **TrueNAS host shell**:

```bash
sudo mkdir -p /mnt/labpool/erpnext-catalog-test/sites /mnt/labpool/erpnext-catalog-test/logs /mnt/labpool/erpnext-catalog-test/db_data /mnt/labpool/erpnext-catalog-test/queue_data
```

Use your actual lab pool name if different, both here and in --lab-root. These
must be NEW, dedicated directories. The permissions helper checks/sets their
ownership. Do not select a shared business directory or existing application data.

## 4. Install the rendered draft

In the VM install via YAML as a NEW app named **erpnext-catalog-test**, using the
complete catalog-dev/generated/catalog-test.yaml output. No changes to old apps.

The startup chain is permissions → bootstrap (copies image site assets into the
dataset) → initializer (configures Frappe and creates site) → runtime. MariaDB
and Redis are also required healthy before initializer. Permissions, bootstrap,
and initializer are one-shot containers, expected to exit with code 0.

Open http://VM-IP:18084. Username: Administrator; password chosen during render.
Complete the setup wizard with fictional information.

If it fails, send the failing service and final log lines. Do not remove guards
or chown broad parent directories to work around failure.

## 5. Verify this new storage/security model

- Fresh install and login.
- CSS, JavaScript and icons load (checks copied site assets).
- Create fictional customer and Issue, attach a harmless file, open it.
- App stop/start; records, assets and attachment remain.
- VM restart; repeat verification.
- Edit/save unchanged YAML; no new site or password reset.
- Existing apps remain unchanged.
- Record whether custom-app mode displays a Web Portal button; lack of a button
  alone does not invalidate the catalog-generated deployment test.

Append results to docs/TEST-RESULTS.md in erpnext-truenas, with a section titled
`Catalog-rendered draft / library 2.3.17`. This draft does not test one-click
catalog updates, form rendering, admission, restore import, or HexOS.

## 6. After this passes

Run official app schema/render validation and metadata generation using a Docker
capable Linux/WSL development environment, following the CURRENT apps CONTRIBUTIONS.md.
Vendor the library with official `devbox run copy-lib`; do not copy it manually.
Review permissions/healthchecks and complete icon/digest/version metadata. Integrate
upgrade lifecycle for this storage model before calling it update-ready.

Open a draft PR only after checking duplicate ERPNext work and discussing scope
with maintainers. There is no need to post automatically or request catalog
acceptance merely to run the local rendered deployment.
