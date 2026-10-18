# VMware and TrueNAS lab

## 1. Build the VM

Suggested allocation on a 32 GB Windows computer: 4 virtual CPUs, 12 GB RAM,
32 GB boot disk, and a separate 100 GB thin-provisioned data disk. These are lab
allocations, not official minimums or production sizing advice.

Use the official TrueNAS 25.10.7 installer. Choose a 64-bit Linux guest profile
in VMware if there is no TrueNAS profile. Match firmware to installer support;
do not pass through physical disks or attach production shares.

Use bridged networking if available; otherwise NAT works if the Windows host can
reach the VM IP. Use a different IP/hostname from production. Install onto the
32 GB disk, then create a pool named `labpool` on the data disk. Configure the
Apps pool in the TrueNAS UI. Power off and take a VMware snapshot before testing.

## 2. Copy the project into GitHub Desktop's repository

Extract the starter ZIP outside the repository. Copy the contents of its
`erpnext-truenas` folder into your existing repository root (alongside `.git`).
Do not replace `.git`. In GitHub Desktop, review Changes, commit the source, and
publish when ready. The generated directory must never appear in the commit.

## 3. Generate and deploy

Run the Windows commands in README.md. In the VM's TrueNAS UI, open Apps,
Discover, then Install via YAML (menu placement can vary). Name the app
`erpnext-test`. Paste all of `generated/erpnext-test.yaml` and install.

Do not use the live NAS for this test. Do not change the generated storage to
point at live folders. Downloading images and building the site can take minutes.

Check logs for `initializer`. Success ends with `ERPNext installation complete.`
Configurator and initializer are one-shot services: exited with code 0 is normal.
Other application services should then run.

Visit `http://VM-IP:18081`. Sign in as `Administrator` using the password entered
in the generator. Site name `erpnext.test` is internal; no DNS setup is necessary.
Complete ERPNext's business setup wizard with fictional test company information.

## 4. Acceptance checks

Record results and log excerpts in `docs/TEST-RESULTS.md`:

1. Fresh install: no shell site-creation commands; login works.
2. Create a fictional customer and Issue; attach a harmless sample file.
3. Stop/start the app. Login, records, and attachment survive.
4. Restart the TrueNAS VM. Repeat verification.
5. Edit/save the same app configuration. No new site or reset password.
6. In initializer logs, check for managed site verification if it reruns.
7. Generate another deployment with `--port 18082 --output generated/second.yaml`;
   install as `erpnext-test-2` and verify it has no first-installation records.

If a service fails, send its name, exit code, and final ~50 log lines. Redact
passwords and tokens. Never send the generated YAML publicly.

## 5. Recovery during prototype tests

Do not rerun generation to change database credentials on existing data. MariaDB
does not reset its stored password simply because an environment variable changes.
Retain the exact YAML used for a test installation.

An interrupted installation intentionally blocks future initialization. Preserve
logs and investigate. To retry from scratch, use a NEW app name and fresh volumes,
or restore the pre-install VM snapshot. Do not delete data on the production NAS.

Automated upgrades and restore procedures are the next milestone, not features of
this prototype. A VMware snapshot is a lab reset mechanism, not a production
application backup strategy.
