import collections
import os
import re
from pathlib import Path

import yaml

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def get_config():
    default = _get_config_from_file('defaults.yml')
    _parse_env_vars(default)
    local = _get_local_config()
    config_dict = _update_dict(default, local)
    docker = _get_docker_config()
    _update_dict(config_dict, docker)
    return default


def _get_config_from_file(file_name, check_if_exists=False):
    config_file = Path(os.path.join(__location__, file_name))
    if config_file.is_file() or not check_if_exists:
        with open(os.path.join(__location__, file_name)) as ymlfile:
            return yaml.safe_load(ymlfile)
    return {}


def _get_local_config():
    is_testing = bool(int(os.environ.get('TESTING', '0')))
    if is_testing:
        file_name = 'local_testing.yml'
    else:
        file_name = 'local.yml'
    return _get_config_from_file(file_name, check_if_exists=True)


def _get_docker_config():
    is_using_docker = bool(int(os.environ.get('DOCKER', '0')))
    if not is_using_docker:
        return {}
    return _get_config_from_file('docker.yml', check_if_exists=True)


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
            pattern = "\\$ENV\\{(.*), (.*)\\}"
            search = re.search(pattern, str(config[k]))
            if search:
                env_var = search.group(1)
                default = search.group(2)
                value = os.getenv(env_var, default)
                if value.isdigit():
                    value = int(value)
                elif value in ['True', 'False']:
                    value = value == 'True'
                config[k] = value
    return config
