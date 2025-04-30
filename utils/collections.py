import os
import yaml


def merge_dict(*dicts):
    """Recursively merge dicts into dest in-place."""
    dest = dicts[0]
    for d in dicts[1:]:
        for key, value in d.items():
            if isinstance(value, dict):
                node = dest.setdefault(key, {})
                merge_dict(node, value)
            else:
                dest[key] = value


def load_yaml(path):
    """Loads yaml files"""
    if not os.path.isfile(path):
        return {}
    with open(path) as fd:
        return yaml.safe_load(fd)
