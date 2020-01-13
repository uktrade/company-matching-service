import pytest

from tests.api.support.utils import assert_search_api_response


@pytest.fixture(scope='module', autouse=True)
def setup_function(app, add_company_description_db):
    app.config['access_control']['hawk_enabled'] = False


def test_update_and_match(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/update/',
            body={
                "descriptions": [
                    {"id": '1', "datetime": "2010-01-01 00:00:00", "source": "dit.datahub",
                     "companies_house_id": "11111111", "company_name": "a"},
                    {"id": '2', "datetime": "2010-01-02 00:00:00", "source": "dit.datahub",
                     "companies_house_id": "22222222", "company_name": "b"},
                    {"id": '3', "datetime": "2010-01-03 00:00:00", "source": "dit.datahub",
                     "companies_house_id": "11111111", "company_name": "b"},
                ],
            },
            expected_response=(200, {'matches': [
                {'id': '1', 'match_id': 2, 'similarity': '101000'},
                {'id': '2', 'match_id': 1, 'similarity': '100000'},
                {'id': '3', 'match_id': 2, 'similarity': '101000'},
            ]})
        )


def test_update(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/update/',
            params='match=false',
            body={
                'descriptions': [
                    {'id': '1', 'datetime': '2010-01-01 00:00:00', 'source': 'dit.datahub',
                     'companies_house_id': '11111111', 'duns_number': '1', 'company_name': 'a'},
                ],
            },
            expected_response=(204, None)
        )


def test_update_missing_required_attribute(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/update/',
            params='match=false',
            body={
                'descriptions': [
                    {'id': '1', 'source': 'dit.datahub', 'companies_house_id': '11111111'},
                ],
            },
            expected_response=(400, {'error': "'datetime' is a required property"})
        )


def test_update_at_least_one_description_attribute_required(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/update/',
            body={
                'descriptions': [
                    {'id': '1', 'datetime': '2010-01-01 00:00:00', 'source': 'dit.datahub'},
                ],
            },
            expected_response=(400, {'error': "'company_name' is a required property"})
        )


def test_update_invalid_contact_email(app):
    with app.test_client() as app_context:
        assert_search_api_response(
            app_context=app_context,
            api='http://localhost:80/api/v1/company/update/',
            body={
                'descriptions': [
                    {'id': '1', 'datetime': '2010-01-01 00:00:00', 'contact_email': 'invalid', 'source': 'dit.datahub'},
                ],
            },
            expected_response=(400, {'error': "'invalid' does not match '[^@]+@[^@]+\\\\.[^@]+'"})
        )
