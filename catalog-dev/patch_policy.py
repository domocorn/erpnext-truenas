"""Explicitly reviewed image pair for the isolated catalog patch experiment."""
SOURCE_DIGEST = 'sha256:f2d409c58ed1b688b6f2914d4a7f8b2468ee60bd1a3f1bd82d6fe32071806cb1'
SOURCE_ID = 'sha256:e43ea1a1aa4bf9a7d01001aaa0120ce564d9af5d10b588064bb8de0aad7ec213'
SOURCE = 'frappe/erpnext:v16.51.0@' + SOURCE_DIGEST
TARGET = 'frappe/erpnext:v16.51.1@sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268'


def validate_patch(source, target, source_digest, observed_id):
    if (source, target, source_digest, observed_id) != (SOURCE, TARGET, SOURCE_DIGEST, SOURCE_ID):
        raise RuntimeError('Only the explicitly reviewed v16.51.0 to v16.51.1 image pair is supported')
