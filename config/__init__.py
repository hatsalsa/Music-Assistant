from pathlib import Path
import yaml
import os

class Config:
    def __init__(self, data: dict):
        self._data = data
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))
            else:
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
    self.root_config = self.package_root
class Files:
  def __init__(self):
    self.root_config = os.path.join(directories.root_config, "config.yml")


directories = Directories()
filenames = Files()


def load_config():
  with open(filenames.root_config) as fd:
    config_data = yaml.safe_load(fd)
    return Config(config_data)

config = load_config()

