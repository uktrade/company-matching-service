import os
from threading import get_ident

import certifi
import redis
import sentry_sdk
from flask import Flask, json
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import scoped_session

from app import config
from app.api.views import api
from app.commands.dev import cmd_group as dev_cmd

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    environment=os.environ.get('ENVIRONMENT'),
    enable_tracing=True,
    # In data hub we have both of these set to 0.01 to reduce load on our Sentry instance
    # but we set it to 1 here initially, to ensure the platform migration is working
    sample_rate=1, # 0.01,
    traces_sample_rate=1, # 0.01, # reduce the number of performance traces
    enable_backpressure_handling=True, # ensure that when sentry is overloaded, we back off and wait
)

def get_or_create():
    from flask import current_app as flask_app

    if not flask_app:
        flask_app = _create_base_app()
    return flask_app


def make_current_app_test_app(test_db_name):
    flask_app = get_or_create()
    postgres_db_config = (
        os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ
        else config.get_config()['app']['database_url']
    )
    flask_app.config.update(
        {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': _create_sql_alchemy_connection_str(
                postgres_db_config, test_db_name
            ),
        }
    )
    return flask_app


def _create_base_app():
    flask_app = Flask(__name__)
    flask_app.config.update(config.get_config())
    flask_app.cli.add_command(dev_cmd)

    postgres_db_config = (
        os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ
        else config.get_config()['app']['database_url']
    ).replace('postgres://', 'postgresql://')
    flask_app.config.update(
        {
            'TESTING': False,
            'SQLALCHEMY_DATABASE_URI': _create_sql_alchemy_connection_str(postgres_db_config),
            # set SQLALCHEMY_TRACK_MODIFICATIONS to False because
            # default of None produces warnings, and track modifications
            # are not required
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        }
    )
    flask_app = _register_components(flask_app)
    return flask_app


def _register_components(flask_app):
    from app.db.models import sql_alchemy
    sql_alchemy.init_app(flask_app)
    flask_app.db = sql_alchemy
    flask_app.register_blueprint(api)
    redis_uri = _get_redis_url(flask_app)
    flask_app.cache = redis.from_url(redis_uri)
    return flask_app


def _create_sql_alchemy_connection_str(cfg, db_name=None):
    if db_name:
        if '?' in cfg:
            cfg = cfg.split('?')[0] + '/' + db_name + cfg.split('?')[-1]
        else:
            cfg += f'/{db_name}'
    url = make_url(cfg)
    return url


def _load_uri_from_vcap_services(service_type):
    if 'VCAP_SERVICES' in os.environ:
        vcap_services = os.environ.get('VCAP_SERVICES')
        services = json.loads(vcap_services)
        if service_type in services:
            services_of_type = services[service_type]
            for service in services_of_type:
                if 'credentials' in service:
                    if 'uri' in service['credentials']:
                        return service['credentials']['uri']
    return None


def _get_redis_url(flask_app):
    redis_uri = _load_uri_from_vcap_services('redis')
    if not redis_uri:
        password = flask_app.config['cache'].get('password')
        redis_uri = (
            f"user:{password}"
            if password
            else "" f"{flask_app.config['cache']['host']}:" f"{flask_app.config['cache']['port']}"
        )
    if redis_uri.startswith('rediss://'):
        return f"{redis_uri}?ssl_ca_certs={certifi.where()}"
    return redis_uri
