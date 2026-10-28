"""Exact image pair for the unvalidated 16.52.1 update candidate."""
SOURCE_VERSION = '16.51.1'
TARGET_VERSION = '16.52.1'
SOURCE_DIGEST = 'sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268'
SOURCE_ID = 'sha256:0ce48f9b465e15869540282c8f203bdbe24b2ae9fe5419c2f32c7e462fba5591'
SOURCE = 'frappe/erpnext:v' + SOURCE_VERSION + '@' + SOURCE_DIGEST
TARGET = 'frappe/erpnext:v16.52.1@sha256:bc21532268c35cec5756c44a11fe510bfccbf23fb4ad651a38644d0c25b56299'


def validate_patch(source, target, source_digest, observed_id):
    if (source, target, source_digest, observed_id) != (SOURCE, TARGET, SOURCE_DIGEST, SOURCE_ID):
        raise RuntimeError('Only the exact candidate v' + SOURCE_VERSION + ' to v' + TARGET_VERSION + ' image pair is supported')
