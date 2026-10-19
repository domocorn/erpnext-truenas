# Upgrade implementation validation

Built against upstream project commit bea7589. Existing user test results were
not overwritten by this update.

11 local unit tests passed on Linux. Two container-only tests are skipped on
Windows because the embedded job uses Linux filesystem locking; nine portable
tests still execute there. Embedded Python and YAML were parsed locally.

Covered: source/target image selection, forbidden version transitions, private
credential/storage/port preservation, offline stage service isolation, startup
guards, simulated pre-migration failure, real command failure state, refusal to
retry unknown partial migrations, and restoration of previous scheduler state.

No Docker engine is available in the authoring runtime. Actual TrueNAS staged
deployment, backup execution and migration remain pending VM testing. A same-tag
rehearsal is not evidence of a real release upgrade.
