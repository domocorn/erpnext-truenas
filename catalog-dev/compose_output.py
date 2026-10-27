"""Readable private YAML with headroom below TrueNAS's WebSocket message limit."""
import copy
import json
import yaml


class LiteralDumper(yaml.SafeDumper):
    pass


def represent_string(dumper, value):
    return dumper.represent_scalar('tag:yaml.org,2002:str', value,
        style='|' if '\n' in value else None)


LiteralDumper.add_representer(str, represent_string)


def compact_document(document):
    result = copy.deepcopy(document)
    used = set()
    for service in result.get('services', {}).values():
        for mount in service.get('configs', []):
            used.add(mount if isinstance(mount, str) else mount['source'])
    if 'configs' in result:
        result['configs'] = {name: value for name, value in result['configs'].items() if name in used}
    return result


def share_equal_nodes(value, cache):
    # Standard YAML anchors share identical mount/dependency/environment blocks.
    # Values still expand to exactly the same Compose mapping when parsed.
    if isinstance(value, dict):
        result = {key: share_equal_nodes(item, cache) for key, item in value.items()}
    elif isinstance(value, list):
        result = [share_equal_nodes(item, cache) for item in value]
    else:
        return value
    key = json.dumps(result, sort_keys=True, separators=(',', ':'))
    return cache.setdefault(key, result)


def dump_private_compose(document):
    result = compact_document(document)
    text = yaml.dump(share_equal_nodes(result, {}), Dumper=LiteralDumper, sort_keys=False, width=120)
    # Leave at least 4 KiB for method/ID/other app.update request fields. Check
    # CRLF too because editors/platforms can change line endings before paste.
    for candidate in (text, text.replace('\n', '\r\n')):
        if len(json.dumps(candidate)) > 60 * 1024:
            raise ValueError('Compose YAML exceeds the safe TrueNAS UI request budget')
    if yaml.safe_load(text) != result:
        raise ValueError('Compose serialization changed document semantics')
    return text
