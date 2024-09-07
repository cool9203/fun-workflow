# coding: utf-8

from functools import partial
from pathlib import Path

from . import _config

env_file_path = "./.env.toml"
if Path(env_file_path).is_file():
    print(f"Load '{env_file_path}' success")
    config = _config.load_config(env_file_path)

config_nested_get = partial(_config.dict_nested_get, config)
