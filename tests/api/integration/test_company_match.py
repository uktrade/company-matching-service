import pytest

from app.db.models import CompaniesHouseIDMapping, CompanyNameMapping
from tests.api.support.utils import assert_search_api_response


@pytest.fixture(scope='module', autouse=True)
def setup_function(app, add_mapping_db):
    app.config['access_control']['hawk_enabled'] = False
    add_mapping_db(
        [
            {
                'companies_house_id': '1rr31111',
                'prev_match_id': 1,
                'match_id': 1,
                'source': 'companies_house.companies',
                'datetime': '2019-01-02 00:00:00',
            },
            {
                'companies_house_id': '1rr41111',
                'prev_match_id': 2,
                'match_id': 2,
                'source': 'companies_house.companies',
                'datetime': '2019-01-02 00:00:00',
            },
        ],
        CompaniesHouseIDMapping,
    )
    add_mapping_db(
        [
            {
                'name_simplified': 'bad corp',
                'prev_match_id': 1,
                'match_id': 1,
                'source': 'companies_house.companies',
                'datetime': '2019-01-02 00:00:00',
            },
            {
                'name_simplified': 'ugly corp',
                'prev_match_id': 1,
                'match_id': 2,
                'source': 'companies_house.companies',
                'datetime': '2019-01-02 00:00:00',
            },
        ],
        CompanyNameMapping,
    )


def test_match(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/match/',
            body={
                'descriptions': [
                    {'id': '1', 'companies_house_id': '1rr31111', 'company_name': 'bad corp'},
                    {'id': '2', 'companies_house_id': '1rr41111'},
                    {'id': '3', 'companies_house_id': '11111111', 'company_name': 'new corp'},
                ],
            },
            expected_response=(
                200,
                {
                    'matches': [
                        {'id': '1', 'match_id': 1, 'similarity': '100000'},
                        {'id': '2', 'match_id': 2, 'similarity': '100000'},
                        {'id': '3', 'match_id': None, 'similarity': '000000'},
                    ]
                },
            ),
        )


def test_match_missing_required_attribute(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/match/',
            body={
                'descriptions': [{'companies_house_id': '1rr31111', 'company_name': 'bad corp'}],
            },
            expected_response=(400, {'error': "'id' is a required property"}),
        )


def test_match_at_least_one_description_attribute_required(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/match/',
            body={'descriptions': [{'id': '1', 'companies_house_id': '1rr31111'}, {'id': '2'}]},
            expected_response=(400, {'error': "'company_name' is a required property"}),
        )


def test_match_invalid_contact_email(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/match/',
            body={'descriptions': [{'id': '1', 'contact_email': 'invalid'}]},
            expected_response=(400, {'error': "'invalid' does not match '[^@]+@[^@]+\\\\.[^@]+'"}),
        )


def test_update_invalid_companies_house_id(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/update/',
            body={
                'descriptions': [
                    {
                        'id': '1',
                        'datetime': '2010-01-01 00:00:00',
                        'companies_house_id': '1234567',
                        'source': 'dit.datahub',
                    },
                ],
            },
            expected_response=(400, {'error': "'1234567' is too short"}),
        )
