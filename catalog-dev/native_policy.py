"""Stable lifecycle identity for catalog-created sites; independent of user secrets."""
import hashlib
import re


def operation_id(site, image):
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,120}', site) or '..' in site:
        raise RuntimeError('Invalid native site identity')
    return hashlib.sha256(('catalog-native-v1\0'+site+'\0'+image).encode()).hexdigest()[:32]
