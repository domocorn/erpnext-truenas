2026-10-26 update: native catalog install/patch/restart and actual failure/independent recovery/restart have now passed by user report. The tested normal lifecycle is integrated into the default draft; exact service/script/image/storage comparison passed except explanatory notes. The investigation below is historical source-review context; current evidence is in ../docs/TEST-RESULTS.md and SUBMISSION-PREPARATION.md. General image upgrades and automatic rollback remain unsupported.

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

## Same-image interruption rehearsal

The dedicated recovery clone now supports a controlled actual migration
interruption test. A test-only wrapper injects a before_migrate hook into the
ephemeral job container, commits a fixture ToDo and waits. Killing only that
container leaves durable migrating state. Local diagnostics confirmed the partial
fixture existed; retry and guarded resume were refused. Recovery is performed
into a new independent destination using the pre-migration backup. This wrapper
is absent from the catalog template and requires explicit test acknowledgement.

This is narrower than a real versioned database patch failure: it does not test
DDL damage, incompatible schemas, external effects or queue draining. Native
catalog integration and automatic rollback remain unsupported. See
CATALOG-INTERRUPTION-TEST.md for the controlled VM procedure.

## One-deployment coordinator prototype

The private prepare_coordinator.py plan replaces the recovered clone's initializer
entrypoint with a coordinator that holds the exclusive runtime lock continuously
across backup, migration, original initialization and durable resume. Runtime
services retain their successful-initializer dependency and operation guards.
Only same-image transitions on the known recovered test clone are accepted.
Completed backup/migration work is reused on repeat; a failed migration blocks
automatic retry, while a failed post-migration resume can repeat without migrating.

Local real-container checks proved live runtime prevents coordinator mutation,
and a stopped-app single deployment completed the sequence. This consolidates
the previously manual stages and exercises their dependency graph. It does not
constitute a native catalog update test, modify the default catalog template or
permit source/target image changes. Source-image backup execution, approved patch
transitions, asset refresh, queue draining and native host integration remain work.
See CATALOG-COORDINATOR-TEST.md for the next VM procedure.

## Warm worker stop and queue gate

Pinned bench CLI uses execv for Frappe commands, so the supervisor's child PID
becomes the RQ worker. RQ's job child ignores SIGINT but resets SIGTERM to default;
forwarding SIGTERM to the whole process group could terminate active work before
the worker drains. The supervisor now signals only the worker PID for bench worker
commands, retaining process-group forwarding for other runtime commands. Both
workers get 120-second stop grace. This matches the pinned source and RQ's
[warm shutdown documentation](https://python-rq.org/docs/workers/).

Under exclusive runtime exclusion, new backup and actual migration now inspect
all registered Redis queues. Queued, started, deferred, scheduled and failed work
blocks the operation before new backup/migrating state is written. Registry reads
use cleanup=False and never auto-expire/remove orphaned work. Already-completed
operations can repeat without migrating or requiring an empty live queue.

Local actual worker/full-app stops let active sleep jobs finish; a deliberately
short forced-stop timeout returned 137 and left started work that the migration
gate refused. This is bounded warm shutdown plus fail-closed queue review, not
an unlimited drain, automatic replay or guarantee of external side effects.
