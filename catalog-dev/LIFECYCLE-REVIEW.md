# Upgrade lifecycle investigation

Reference target: TrueNAS 25.10.7. This is source review, not a successful native
catalog upgrade test.

The versioned [upgrade implementation](https://github.com/truenas/middleware/blob/TS-25.10.7/src/middlewared/middlewared/plugins/apps/upgrade.py)
calls app.stop before rendering and starting a native catalog upgrade. Its custom
app branch instead delegates to image pulling/redeployment. Host-path snapshots
depend on the selected option and identifiable datasets; directories alone do not
establish a recoverable snapshot.

The versioned [Compose implementation](https://github.com/truenas/middleware/blob/TS-25.10.7/src/middlewared/middlewared/plugins/apps/compose_utils.py)
performs down before up when force_recreate is requested. This supports a stopped
boundary in that native path. It does not establish behavior for future releases,
direct Docker commands, every custom-app edit, or a completed application backup.

## Runtime exclusion implemented before migration

Every ERPNext runtime service now runs through a non-root supervisor that:

- Acquires a shared sites/.catalog-runtime.lock for its complete child lifetime.
- Verifies the catalog site/image markers and completed initialization.
- Rejects upgrade state unless the expected operation matches, its target equals
  the running image, and its persisted status is resumed.
- Preserves the official image entrypoint, passing its original service command.
- Forwards SIGTERM/SIGINT to the child process group and returns its exit status.

A future backup/migration job must take an exclusive lock on the SAME file before
examining or changing state. Lock acquisition failure must abort, not steal/delete
the lock. OS locks release with process exit; a leftover filename is harmless.

All existing runtime containers must first adopt this guard. Legacy containers
do not hold this lock; acquiring it cannot prove those containers are stopped.
The rollout therefore requires stopping the app before applying the same-image
guard revision. The native update order remains a separate integration check.

The current bootstrap continues to reject image changes. This revision does not
run backups, patch a database, permit image upgrades, or provide rollback. Graceful
signal forwarding is tested; complete job draining before Docker's stop timeout
is not established. Old in-flight RQ work and restore of queue state need explicit
testing before native upgrades are supported.

## Additional custom-app edit source check

In the same version's [CRUD implementation](https://github.com/truenas/middleware/blob/TS-25.10.7/src/middlewared/middlewared/plugins/apps/crud.py),
update_internal uses force_recreate when it triggers Compose for an edited app,
including custom apps. Editing an already stopped app does not trigger Compose;
it must be started afterward. The VM rehearsal checks this path in practice.
