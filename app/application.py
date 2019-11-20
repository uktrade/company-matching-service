import os

import redis
from flask import Flask, json
from sqlalchemy.engine.url import URL, make_url

from app import config
from app.api.views import api


def get_or_create():
    from flask import current_app as flask_app
    if not flask_app:
        flask_app = _create_base_app()
    return flask_app


def make_current_app_test_app(test_db_name):
    flask_app = get_or_create()
    postgres_db_config = os.environ.get('DATABASE_URL') if 'DATABASE_URL' in os.environ \
        else config.get_config()['database']
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': _create_sql_alchemy_connection_str(postgres_db_config, test_db_name)
    })
    flask_app.config['database']['use-db'] = test_db_name
    return flask_app


def _create_base_app():
    flask_app = Flask(__name__)
    flask_app.config.update(config.get_config())
    db_config = os.environ.get('DATABASE_URL') if 'DATABASE_URL' in os.environ \
        else config.get_config()['database']

    flask_app.config.update({
        'TESTING': False,
        'SQLALCHEMY_DATABASE_URI': _create_sql_alchemy_connection_str(db_config),
        # set SQLALCHEMY_TRACK_MODIFICATIONS to False because
        # default of None produces warnings, and track modifications
        # are not required
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    flask_app = _register_components(flask_app)
    return flask_app


def _register_components(flask_app):
    from app.db import sql_alchemy
    sql_alchemy.session = sql_alchemy.create_scoped_session()
    sql_alchemy.init_app(flask_app)
    flask_app.db = sql_alchemy
    flask_app.register_blueprint(api)
    redis_uri = _load_uri_from_vcap_services(service_type='redis')
    if redis_uri:
        flask_app.cache = redis.from_url(redis_uri)
    else:
        flask_app.cache = redis.Redis(
            host=flask_app.config['cache']['host'],
            port=flask_app.config['cache']['port'],
            password=None if flask_app.config['cache']['password'] == '' else flask_app.config['cache']['password'],
            ssl=flask_app.config['cache']['ssl'],
        )

    return flask_app


def _create_sql_alchemy_connection_str(cfg, db_name=None):
    if type(cfg) is dict:
        return URL(cfg['dialect'], cfg['user'], cfg['password'], cfg['host'], cfg['port'], db_name or cfg['use-db'])
    else:
        url = make_url(cfg)
        if db_name:
            url.database = db_name
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
