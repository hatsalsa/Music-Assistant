import os
from pathlib import Path
import yaml
from utils.collections import merge_dict

class Config:
    def __init__(self, data: dict):
        self._data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                value = Config(value)  # recursively wrap
            self._data[key] = value
            setattr(self, key, value)

    def __getattr__(self, item):
        if item in self._data:
            return self._data[item]
        raise AttributeError(f"'{item}' not found in config")

    def __getitem__(self, item):
        return self._data[item]


class Directories:
    def __init__(self):
        self.package_root = Path(__file__).resolve().parent.parent
        self.root_config = self.package_root / "config"
        self.user_configs = self.package_root
        self.tracker_configs = self.user_configs / "trackers"


class Files:
    def __init__(self):
        self.root_config = os.path.join(directories.root_config, "config.yml")
        self.user_root_config = os.path.join(directories.user_configs, "config.yml")
        self.tracker_config = os.path.join(directories.root_config, "trackers", "{tracker}.yml")
        self.user_tracker_config = os.path.join(directories.tracker_configs, "{tracker}.yml")


directories = Directories()
filenames = Files()
with open(filenames.root_config) as fd:
    config = yaml.safe_load(fd)
with open(filenames.user_root_config) as fd:
    user_config = yaml.safe_load(fd)

merge_dict(config, user_config)
config = Config(config)

# Old version of loading yml files.
# def load_config():
#   with open(filenames.root_config) as fd:
#     config_data = yaml.safe_load(fd)
#     return Config(config_data)
#
# config = load_config()
