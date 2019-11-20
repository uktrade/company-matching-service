import sqlalchemy_utils
from flask import current_app as app
from flask_script import Manager

from app.db.models import CompanyDescriptionModel, sql_alchemy, create_sequences, CompaniesHouseIDMapping, \
    DunsNumberMapping, CompanyNameMapping, ContactEmailMapping, CDMSRefMapping, PostcodeMapping

DevCommand = Manager(app=app, usage='Development commands')


@DevCommand.option(
    '--create',
    dest='create',
    action='store_true',
    help='Create database using database name specified in (local) config')
@DevCommand.option(
    '--drop',
    dest='drop',
    action='store_true',
    help='Drop database using database name specified in (local) config')
@DevCommand.option(
    '--create_tables',
    dest='tables',
    action='store_true',
    help='Create database tables')
def db(create=False, drop=False, tables=False):
    if not drop and not create and not tables:
        print('please choose an option (--drop, --create or --create_tables)')
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    db_name = db_url.database
    if drop:
        print(f'Dropping {db_name} database')
        sqlalchemy_utils.drop_database(db_url )
    if create:
        print(f'Creating {db_name} database')
        sqlalchemy_utils.create_database(db_url, encoding='utf8')
    if create or tables:
        print('Creating DB tables')
        CompanyDescriptionModel.__table__.create(sql_alchemy.engine, checkfirst=True)
        CompaniesHouseIDMapping.__table__.create(sql_alchemy.engine, checkfirst=True)
        DunsNumberMapping.__table__.create(sql_alchemy.engine, checkfirst=True)
        CompanyNameMapping.__table__.create(sql_alchemy.engine, checkfirst=True)
        ContactEmailMapping.__table__.create(sql_alchemy.engine, checkfirst=True)
        CDMSRefMapping.__table__.create(sql_alchemy.engine, checkfirst=True)
        PostcodeMapping.__table__.create(sql_alchemy.engine, checkfirst=True)
        print('Creating DB sequences')
        create_sequences()
