# Delivery milestones

1. **Current:** standalone custom-app lab prototype. Validate installation,
   initial setup, restart persistence, isolation, and failure logs on 25.10.7.
2. Backup and restore: database, public/private files, site config and encryption
   key. Restore into fresh storage and verify attachments/encrypted configuration.
3. Upgrade orchestration: stop/drain workers and prevent writes, preserve backup,
   configure new image, migrate, then start services. Test failure blocking and
   recovery using matching code and data. Compose dependencies alone do not prove
   old containers have stopped before database migration.
4. TrueNAS package: follow the CURRENT `truenas/apps` contribution guide and
   library conventions. Build metadata, ix_values, questions, templates, test
   values, portal and permissions. Test rendering and actual deployment. A ZIP
   cannot be imported into Discover as a catalog app.
5. Review existing ERPNext issues/PRs; discuss scope; submit a community-train
   draft PR after local validation. Catalog publication requires acceptance.
6. Existing installation import: test backup/restore from the current live image
   into a separate new deployment. Never concurrently mount a live database.
7. HexOS: use its current supported curation examples and development interface;
   keep its wrapper thin, with shared initialization/update behavior. Test on an
   actual HexOS instance, then submit for review. TrueNAS support alone does not
   guarantee HexOS compatibility or curation acceptance.

Do not claim one-click upgrades until a version transition, a failed transition,
and a restore have all been tested.
