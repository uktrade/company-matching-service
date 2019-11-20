import collections
import os
import re
from pathlib import Path

import yaml

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def get_config():
    default = _get_default_config()
    _parse_env_vars(default)
    local = _get_local_config()
    _update_dict(default, local)
    return default


def _get_default_config():
    with open(os.path.join(__location__, 'defaults.yml')) as ymlfile:
        return yaml.safe_load(ymlfile)


def _get_local_config():
    is_testing = bool(int(os.environ.get('TESTING', '0')))
    if is_testing:
        file_name = 'local_testing.yml'
    else:
        file_name = 'local.yml'
    local_config = Path(os.path.join(__location__, file_name))
    if local_config.is_file():
        with open(os.path.join(__location__, file_name)) as ymlfile:
            return yaml.safe_load(ymlfile)
    return {}


def _update_dict(dest, source):
    for k, v in source.items():
        if isinstance(v, collections.Mapping):
            sub_dict = _update_dict(dest.get(k, {}), v)
            dest[k] = sub_dict
        else:
            dest[k] = source[k]
    return dest


def _parse_env_vars(config):
    for k, v in config.items():
        if isinstance(v, collections.Mapping):
            _parse_env_vars(v)
        if isinstance(v, list):
            for item in v:
                _parse_env_vars(item)
        else:
            pattern = "\$ENV\{(.*), (.*)\}"
            search = re.search(pattern, str(config[k]))
            if search:
                env_var = search.group(1)
                default = search.group(2)
                value = os.getenv(env_var, default)
                if value.isdigit():
                    value = int(value)
                elif value in ['True', 'False']:
                    value = (value == 'True')
                config[k] = value
    return config
