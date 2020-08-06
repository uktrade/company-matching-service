import datetime

import pytest
import sqlalchemy_utils

from app import application
from app.db.models import create_sequences

TESTING_DB_NAME_TEMPLATE = 'cms_test_{}'


@pytest.fixture(scope='session')
def app():
    db_name = _create_testing_db_name()
    app = application.make_current_app_test_app(db_name)
    app.config['access_control']['hawk_enabled'] = False
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture(scope='session')
def test_client(app):
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope='function')
def app_with_db(app):
    app.db.session.close_all()
    app.db.engine.dispose()
    sqlalchemy_utils.create_database(app.config['SQLALCHEMY_DATABASE_URI'],)
    app.db.create_all()
    create_sequences()
    yield app
    app.db.session.close()
    app.db.session.remove()
    app.db.drop_all()
    sqlalchemy_utils.drop_database(app.config['SQLALCHEMY_DATABASE_URI'])


@pytest.fixture(scope='module')
def app_with_db_module(app):
    app.db.session.close_all()
    app.db.engine.dispose()
    sqlalchemy_utils.create_database(app.config['SQLALCHEMY_DATABASE_URI'],)
    app.db.create_all()
    create_sequences()
    yield app
    app.db.session.close()
    app.db.session.remove()
    app.db.drop_all()
    sqlalchemy_utils.drop_database(app.config['SQLALCHEMY_DATABASE_URI'])


def _create_testing_db_name():
    time_str = _create_current_time_str()
    return TESTING_DB_NAME_TEMPLATE.format(time_str)


def _create_current_time_str():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d_%H%M%S_%f')
