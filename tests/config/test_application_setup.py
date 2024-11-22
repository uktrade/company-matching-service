import os

from app import application
from unittest import mock
from redis.connection import Connection, SSLConnection

DATABASE_CREDENTIALS = '{"username": "application_user", "password": "p4s5w0rd!", "engine": "postgres", "port": 5432, "dbname": "main", "host": "hostname.rds.amazonaws.com", "dbInstanceIdentifier": "db-instance"}'
DATABASE_URL = 'postgresql://postgres_username:postgres_password@postgres_host:5432/db_name'
DEFAULT_DATABASE_URL = 'postgresql://postgres:postgres@cms_postgres/postgres'
VCAP_SERVICES = '{"redis": [{"credentials": {"host": "master.cf-name.a7xrdh.euw2.cache.amazonaws.com", "name": "cf-name", "password": "password", "port": 6379, "tls_enabled": true, "uri": "rediss://:password@master.cf-name.a7xrdh.euw2.cache.amazonaws.com:6379"}}]}'
REDIS_ENDPOINT = 'rediss://node.identity.cache.amazonaws.com:6379'

def test_default_database_connection_url():
    app = application._create_base_app()
    default_connection_strings = ['postgresql://postgres:***@cms_postgres/postgres', 'postgresql://postgres@localhost/circle_test?sslmode=disable']
    assert str(app.config['SQLALCHEMY_DATABASE_URI']) in default_connection_strings

@mock.patch.dict(os.environ, {"DATABASE_URL": DATABASE_URL})
def test_gov_paas_database_connection_url():
    app = application._create_base_app()
    assert str(app.config['SQLALCHEMY_DATABASE_URI']) == 'postgresql://postgres_username:***@postgres_host:5432/db_name'


@mock.patch.dict(os.environ, {"DATABASE_CREDENTIALS": DATABASE_CREDENTIALS})
def test_dbt_paas_database_connection_url():
    app = application._create_base_app()
    assert str(app.config['SQLALCHEMY_DATABASE_URI']) == 'postgresql://application_user:***@hostname.rds.amazonaws.com:5432/main'


def test_default_redis_connection():
    app = application._create_base_app()
    redis_conn = app.cache.connection_pool.connection_kwargs
    assert redis_conn['host'] == 'cms_redis'
    assert redis_conn['port'] == 6379
    assert app.cache.connection_pool.connection_class == Connection


@mock.patch.dict(os.environ, {"VCAP_SERVICES": VCAP_SERVICES})
def test_gov_paas_redis_connection():
    app = application._create_base_app()
    redis_conn = app.cache.connection_pool.connection_kwargs
    assert redis_conn['host'] == 'master.cf-name.a7xrdh.euw2.cache.amazonaws.com'
    assert redis_conn['port'] == 6379
    assert app.cache.connection_pool.connection_class == SSLConnection


@mock.patch.dict(os.environ, {"REDIS_ENDPOINT": REDIS_ENDPOINT})
def test_dbt_paas_redis_connection():
    app = application._create_base_app()
    redis_conn = app.cache.connection_pool.connection_kwargs
    assert redis_conn['host'] == 'node.identity.cache.amazonaws.com'
    assert redis_conn['port'] == 6379
    assert app.cache.connection_pool.connection_class == SSLConnection
