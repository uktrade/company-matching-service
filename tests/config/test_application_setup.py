import os

from app import application
from unittest import mock

DATABASE_CREDENTIALS = '{"username": "application_user", "password": "p4s5w0rd!", "engine": "postgres", "port": 5432, "dbname": "main", "host": "hostname.rds.amazonaws.com", "dbInstanceIdentifier": "db-instance"}'
DATABASE_URL = 'postgresql://postgres_username:postgres_password@postgres_host:5432/db_name'
DEFAULT_DATABASE_URL = 'postgresql://postgres:postgres@cms_postgres/postgres'


def test_default_database_connection_url():
    app = application._create_base_app()
    assert str(app.config['SQLALCHEMY_DATABASE_URI']) == 'postgresql://postgres:***@cms_postgres/postgres'


@mock.patch.dict(os.environ, {"DATABASE_URL": DATABASE_URL})
def test_gov_paas_database_connection_url():
    app = application._create_base_app()
    assert str(app.config['SQLALCHEMY_DATABASE_URI']) == 'postgresql://postgres_username:***@postgres_host:5432/db_name'


@mock.patch.dict(os.environ, {"DATABASE_CREDENTIALS": DATABASE_CREDENTIALS})
def test_dbt_paas_database_connection_url():
    app = application._create_base_app()
    assert str(app.config['SQLALCHEMY_DATABASE_URI']) == 'postgresql://application_user:***@hostname.rds.amazonaws.com:5432/main'
