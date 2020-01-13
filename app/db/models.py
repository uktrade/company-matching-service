from flask import current_app as app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, DDL
from sqlalchemy.sql import ClauseElement

db = SQLAlchemy()
sql_alchemy = db

# aliases
_sa = sql_alchemy
_col = db.Column
_text = db.Text
_int = db.Integer
_dt = db.DateTime
_bool = db.Boolean
_num = db.Numeric


class BaseModel(db.Model):
    __abstract__ = True

    def save(self):
        _sa.session.add(self)
        _sa.session.commit()

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        """
        Creates a new object or returns existing.

        Example:
            object, created = Model.get_or_create(a=1, b=2, defaults=dict(c=3))

        :param defaults: (dictionary) of fields that should be saved on new instance
        :param kwargs: fields to query for an object
        :return: (Object, boolean) (Object, created)
        """
        instance = _sa.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
            params.update(defaults or {})
            instance = cls(**params)
            instance.save()
            return instance, True


def create_sequences():
    stmt = f'CREATE SEQUENCE IF NOT EXISTS match_id_seq'
    app.db.engine.execute(DDL(stmt))
    stmt = f'CREATE SEQUENCE IF NOT EXISTS company_description_id_seq'
    app.db.engine.execute(DDL(stmt))


class CompanyDescriptionModel(BaseModel):

    __tablename__ = 'company_description'
    __table_args__ = {'schema': 'public'}

    id = _col(_int, primary_key=True)
    source = _col(_text, nullable=False)
    datetime = _col(_dt, nullable=False)
    companies_house_id = _col(_text)
    duns_number = _col(_text)
    company_name = _col(_text)
    contact_email = _col(_text)
    cdms_ref = _col(_text)
    postcode = _col(_text)


class CompaniesHouseIDMapping(BaseModel):

    __tablename__ = 'companies_house_id_mapping'
    __table_args__ = {'schema': 'public'}

    companies_house_id = _col(_text, primary_key=True)
    match_id = _col(_int)
    id = _col(_int, ForeignKey(CompanyDescriptionModel.id))


class DunsNumberMapping(BaseModel):

    __tablename__ = 'duns_number_mapping'
    __table_args__ = {'schema': 'public'}

    duns_number = _col(_text, primary_key=True)
    match_id = _col(_int)
    id = _col(_int, ForeignKey(CompanyDescriptionModel.id))


class CompanyNameMapping(BaseModel):

    __tablename__ = 'company_name_mapping'
    __table_args__ = {'schema': 'public'}

    name_simplified = _col(_text, primary_key=True)
    match_id = _col(_int)
    id = _col(_int, ForeignKey(CompanyDescriptionModel.id))


class ContactEmailMapping(BaseModel):

    __tablename__ = 'contact_email_mapping'
    __table_args__ = {'schema': 'public'}

    contact_email_domain = _col(_text, primary_key=True)
    match_id = _col(_int)
    id = _col(_int, ForeignKey(CompanyDescriptionModel.id))


class CDMSRefMapping(BaseModel):

    __tablename__ = 'cdms_ref_mapping'
    __table_args__ = {'schema': 'public'}

    cdms_ref_cleaned = _col(_text, primary_key=True)
    match_id = _col(_int)
    id = _col(_int, ForeignKey(CompanyDescriptionModel.id))


class PostcodeMapping(BaseModel):

    __tablename__ = 'postcode_mapping'
    __table_args__ = {'schema': 'public'}

    postcode = _col(_text, primary_key=True)
    match_id = _col(_int)
    id = _col(_int, ForeignKey(CompanyDescriptionModel.id))
