import pytest

from app.db.models import CompanyDescriptionModel


@pytest.fixture(scope='module')
def add_company_description_db(app_with_db_module):
    def _method(company_description):
        for description in company_description:
            defaults = {
                'data_hash': description.get('data_hash', None),
                'source': description.get('source', None),
                'datetime': description.get('datetime', None),
                'company_name': description.get('company_name', None),
                'companies_house_id': description.get('companies_house_id', None),
                'duns_number': description.get('duns_number', None),
                'contact_email': description.get('contact_email', None),
                'postcode': description.get('postcode', None),
                'cdms_ref': description.get('cdms_ref', None),
            }
            CompanyDescriptionModel.get_or_create(id=description.get('id', None), defaults=defaults)
    return _method


@pytest.fixture(scope='module')
def add_mapping_db(app_with_db_module):
    def _method(mappings, model):
        for mapping in mappings:
            field = [key for key in mapping.keys() if key not in ['match_id', 'id']][0]
            defaults = {
                'match_id': mapping.get('match_id', None),
                'id': mapping.get('id', None),
            }
            model.get_or_create(
                **{field: mapping.get(field, None)},
                defaults=defaults
            )
    return _method

