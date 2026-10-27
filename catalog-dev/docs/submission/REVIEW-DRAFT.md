# Draft contribution description — NOT POSTED

Proposed title: Draft: Add ERPNext to the community catalog

Adds a single-site ERPNext 16.51.1 package using the TrueNAS 2.3.17 library for
storage permissions, MariaDB, ports and portals. The graph includes Redis cache
and queue services, bootstrap/initializer/source-image backup jobs, backend,
frontend, websocket, two workers and scheduler. Images are digest-pinned.

Managed storage records the site and image identity. Runtime holds shared storage
locks; initialization, backup and migration require exclusive access. Native
upgrades stop the old application before backing up with its original image and
migrating with the target image. A persistent operation state prevents repeated
migration or runtime startup after an incomplete transition. Queue checks refuse
pending/failed work without clearing it, and workers have a 120-second warm-stop
grace period. Only the reviewed 16.51.0 -> 16.51.1 digest pair is enabled.

Validation:

- User-reported TrueNAS 25.10.7 / amd64 native catalog install, patch upgrade,
  preserved record/private attachment, login and unchanged restart passed.
- An actual deliberately failing native migration committed a test record and
  remained blocked after restart. Independent old-image recovery preserved the
  original record/private attachment and decrypted a synthetic encrypted value;
  the failed-migration record was absent. Recovery restart passed. These VM checks
  are user-reported; earlier equivalent Docker checks were performed locally.
- The integrated default template's services/scripts/images/storage/dependencies
  match the tested normal graph. Only explanatory notes differ.
- Linux lifecycle/state/restore/isolation/render regressions passed. Official
  scoped development schema, library hash/vendor output, rendering and Compose
  validation passed. Generated metadata fields were derived with the official
  analyzer; full metadata validation remains blocked on the icon URL.

Icon: attach catalog-dev/assets/erpnext-logo.png from the development repository.
It is the unmodified upstream ERPNext asset, with provenance and SHA256 recorded
in assets/README.md. Please upload the accepted artwork to the TrueNAS CDN and
provide its URL. The metadata deliberately retains an empty icon instead of
claiming that the currently nonexistent CDN URL is available.

Review requested: suitability of the multi-service initialization/backup/migrate
lifecycle and the policy for future image updates. All other upgrades remain
blocked until their image pair and recovery path are reviewed. This initial
package does not offer a general import/restore UI, major upgrades, automatic
rollback, real external-integration credential assurance or HexOS curation.

Related requests: https://github.com/truenas/apps/issues/174 (open) and
https://github.com/truenas/apps/issues/3496 (closed), checked 2026-10-26. The current
GitHub issue search returned no ERPNext pull request; search again when opening
the draft because that can change.

Do not include private generated YAML, backup archives, site configuration or
VM recovery input directories in the contribution. This description remains
unposted; opening the PR is separate from pushing the development branches.
