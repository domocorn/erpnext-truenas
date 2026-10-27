# Image pinning review

Update 2026-10-19: ERPNext tag-to-digest transition and independent recovery of
its backup passed in the VM by user report. The recovery app also reported
MariaDB config ID c1d04d5c27cfe84c85c8b11684d121b93df541ee2ccfdf62f72f2ac4ff37f762
and Redis config ID 166f6f1437e3ae4bb78589379bc6e7937ea6e9fdd93fbb6cdf3a7fd509ca7c9e.
Their RepoDigests match the table below. Registry inspection of each index's
linux/amd64 manifest confirms those config IDs. Both Redis services agree.
The catalog fresh-install defaults now include these digest pins, plus the
verified ERPNext digest. No existing generated deployment was rewritten.
Other architectures have not been runtime-tested. The original investigation
below explains why a tagged deployment needs an explicit identity transition.

The disposable WSL lab used linux/amd64 and pulled these tag digests:

| Image | Observed repository digest |
| --- | --- |
| frappe/erpnext:v16.51.1 | sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268 |
| mariadb:11.8 | sha256:f16d7a344413e519dff518f27bdb221388f84b0d274c97c4fb5f2cb0dc1b34fa |
| redis:8.6-alpine | sha256:ac2da09bc822f325a9f68f533120b86fa39c1b8db46b3aa7c1bbea7fdfd4fcba |

These were initially observed local identities; subsequent VM proof is recorded
above. Runtime tags were deliberately preserved in the earlier healthcheck update.
The permissions utility already has an immutable digest in ix_values.yaml.

ERPNext bootstrap persists repository:tag as its image identity. Appending a
digest would change that identity and block existing storage even if the bytes
were identical. Do not silently strip digests or rewrite the marker to allow it:
that could admit a different image under the same tag without migration.

Before moving this draft to digest pins, compare the exact installed VM image ID
and RepoDigests, define a verified transition from the legacy marker, and test it
alongside upgrade coordination. Pin MariaDB and Redis for the same release;
changing their floating tags can also change persisted-data behavior. Recheck
current catalog image and architecture policies before submission.
