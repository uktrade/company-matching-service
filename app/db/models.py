from flask import current_app as app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DDL, Index
from sqlalchemy.sql import ClauseElement

db = SQLAlchemy()
sql_alchemy = db

# aliases
_sa = sql_alchemy
_col = db.Column
_array = db.ARRAY
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


class CompaniesHouseIDMapping(BaseModel):

    __tablename__ = 'companies_house_id_mapping'

    companies_house_id = _col(_text, primary_key=True)
    prev_match_id = _col(_int, nullable=False)
    match_id = _col(_int, nullable=False)
    source = _col(_text, nullable=False)
    datetime = _col(_dt, nullable=False)

    __table_args__ = (
        Index('companies_house_id_idx', 'companies_house_id', postgresql_using='hash'),
    )


class DunsNumberMapping(BaseModel):

    __tablename__ = 'duns_number_mapping'

    duns_number = _col(_text, primary_key=True)
    prev_match_id = _col(_int, nullable=False)
    match_id = _col(_int, nullable=False)
    source = _col(_text, nullable=False)
    datetime = _col(_dt, nullable=False)

    __table_args__ = (Index('duns_number_idx', 'duns_number', postgresql_using='hash'),)


class CompanyNameMapping(BaseModel):

    __tablename__ = 'company_name_mapping'

    company_name = _col(_text, primary_key=True)
    prev_match_id = _col(_int, nullable=False)
    match_id = _col(_int, nullable=False)
    source = _col(_text, nullable=False)
    datetime = _col(_dt, nullable=False)

    __table_args__ = (Index('company_name_idx', 'company_name', postgresql_using='hash'),)


class ContactEmailMapping(BaseModel):

    __tablename__ = 'contact_email_mapping'

    contact_email = _col(_text, primary_key=True)
    prev_match_id = _col(_int, nullable=False)
    match_id = _col(_int, nullable=False)
    source = _col(_text, nullable=False)
    datetime = _col(_dt, nullable=False)

    __table_args__ = (Index('contact_email_idx', 'contact_email', postgresql_using='hash'),)


class CDMSRefMapping(BaseModel):

    __tablename__ = 'cdms_ref_mapping'

    cdms_ref = _col(_text, primary_key=True)
    prev_match_id = _col(_int, nullable=False)
    match_id = _col(_int, nullable=False)
    source = _col(_text, nullable=False)
    datetime = _col(_dt, nullable=False)

    __table_args__ = (Index('cdms_ref_idx', 'cdms_ref', postgresql_using='hash'),)


class PostcodeMapping(BaseModel):

    __tablename__ = 'postcode_mapping'

    postcode = _col(_text, primary_key=True)
    prev_match_id = _col(_int, nullable=False)
    match_id = _col(_int, nullable=False)
    source = _col(_text, nullable=False)
    datetime = _col(_dt, nullable=False)

    __table_args__ = (Index('postcode_idx', 'postcode', postgresql_using='hash'),)


class HawkUsers(BaseModel):

    __tablename__ = 'hawk_users'
    __table_args__ = {'schema': 'public'}

    id = _col(_text, primary_key=True)
    key = _col(_text)
    scope = _col(_array(_text))
    description = _col(_text)

    @classmethod
    def get_client_key(cls, client_id):
        query = _sa.session.query(cls.key).filter(cls.id == client_id)
        result = query.first()
        return result[0] if result else None

    @classmethod
    def get_client_scope(cls, client_id):
        query = _sa.session.query(cls.scope).filter(cls.id == client_id)
        result = query.first()
        return result[0] if result else None

    @classmethod
    def add_user(cls, client_id, client_key, client_scope, description):
        cls.get_or_create(
            id=client_id,
            defaults={'key': client_key, 'scope': client_scope, 'description': description},
        )
