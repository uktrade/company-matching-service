import pytest

from app.db.models import CompaniesHouseIDMapping, CompanyNameMapping, DunsNumberMapping
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
                'duns_number': 'dun1',
                'prev_match_id': 1,
                'match_id': 1,
                'source': 'dnb.companies.uk',
                'datetime': '2019-01-02 00:00:00',
            },
        ],
        DunsNumberMapping,
    )
    add_mapping_db(
        [
            {
                'company_name': 'bad corp',
                'prev_match_id': 1,
                'match_id': 1,
                'source': 'companies_house.companies',
                'datetime': '2019-01-02 00:00:00',
            },
            {
                'company_name': 'ugly corp',
                'prev_match_id': 1,
                'match_id': 2,
                'source': 'companies_house.companies',
                'datetime': '2019-01-02 00:00:00',
            },
        ],
        CompanyNameMapping,
    )


@pytest.mark.parametrize(
    'params,body,expected_response',
    (
        #   Test match
        (
            None,
            {
                'descriptions': [
                    {'id': '1', 'companies_house_id': '1rr31111', 'company_name': 'bad corp'},
                    {'id': '2', 'companies_house_id': '1rr41111'},
                    {'id': '3', 'companies_house_id': '11111111', 'company_name': 'new corp'},
                ],
            },
            (
                200,
                {
                    'matches': [
                        {'id': '1', 'match_id': 1, 'similarity': '100000'},
                        {'id': '2', 'match_id': 2, 'similarity': '100000'},
                        {'id': '3', 'match_id': None, 'similarity': '000000'},
                    ]
                },
            ),
        ),
        #   Test dnb match
        (
            'dnb_match=true',
            {
                'descriptions': [
                    {'id': '1', 'companies_house_id': '1rr31111', 'duns_number': 'dun1'},
                    {'id': '2', 'companies_house_id': '1rr41111'},
                ],
            },
            (
                200,
                {
                    'matches': [
                        {'id': '1', 'match_id': 'dun1', 'similarity': '110000'},
                        {'id': '2', 'match_id': None, 'similarity': '100000'},
                    ]
                },
            ),
        ),
        #   Test missing required attribute
        (
            None,
            {'descriptions': [{'companies_house_id': '1rr31111', 'company_name': 'bad corp'}]},
            (400, {'error': "'id' is a required property"}),
        ),
        #   Test at least one description attribute required
        (
            None,
            {'descriptions': [{'id': '1', 'companies_house_id': '1rr31111'}, {'id': '2'}]},
            (400, {'error': "'company_name' is a required property"}),
        ),
        #   Test invalid contact email
        (
            None,
            {'descriptions': [{'id': '1', 'contact_email': 'invalid'}]},
            (400, {'error': "'invalid' does not match '[^@]+@[^@]+\\\\.[^@]+'"}),
        ),
        #   Test invalid companies_house_id
        (
            None,
            {
                'descriptions': [
                    {
                        'id': '1',
                        'datetime': '2010-01-01 00:00:00',
                        'companies_house_id': '1234567',
                        'source': 'dit.datahub',
                    },
                ],
            },
            (400, {'error': "'1234567' is too short"}),
        ),
    ),
)
def test_match(params, body, expected_response, app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/match/',
            params=params,
            body=body,
            expected_response=expected_response,
        )
