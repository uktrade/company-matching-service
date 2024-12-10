import os
import json
import requests
from mohawk import Sender

# GOV_PAAS_MATCHING_SERVICE_BASE_URL = os.environ.get("MATCHING_SERVICE_BASE_URL")
# GOV_PAAS_MATCHING_SERVICE_BASE_URL = "http://localhost:5080"
GOV_PAAS_MATCHING_SERVICE_BASE_URL = "https://company-matching-service-staging.london.cloudapps.digital"
DBT_PAAS_MATCHING_SERVICE_BASE_URL = "https://company-matching.prod.uktrade.digital"
HAWK_CLIENT_ID = os.environ.get("HAWK_CLIENT_ID")
HAWK_CLIENT_KEY = os.environ.get("HAWK_CLIENT_KEY")
HAWK_CREDENTIALS = {
    "id": HAWK_CLIENT_ID,
    "key": HAWK_CLIENT_KEY,
    "algorithm": "sha256",
}


def _hawk_api_request(
    url: str,
    method: str,
    query: dict,
    credentials: dict,
    expected_response_structure: str = None,
):
    body = json.dumps(query)
    header = Sender(
        credentials, url, method.lower(), content_type="application/json", content=body
    ).request_header

    response = requests.request(
        method,
        url,
        data=body,
        headers={"Authorization": header, "Content-Type": "application/json"},
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise

    response_json = response.json()
    if expected_response_structure and expected_response_structure not in response_json:
        raise ValueError("Unexpected response structure")

    return response_json


def test_match():
    descriptions = [
        {'id': '1', 'companies_house_id': '1rr31111', 'company_name': 'bad corp'}
    ]

    request = {'descriptions': descriptions}
    match_type = "match"
    gov_paas_data = _hawk_api_request(
        url=f'{GOV_PAAS_MATCHING_SERVICE_BASE_URL}/api/v1/company/{match_type}/',
        method='POST',
        query=request,
        credentials=HAWK_CREDENTIALS,
        expected_response_structure='matches',
    )
    dbt_paas_data = _hawk_api_request(
        url=f'{DBT_PAAS_MATCHING_SERVICE_BASE_URL}/api/v1/company/{match_type}/',
        method='POST',
        query=request,
        credentials=HAWK_CREDENTIALS,
        expected_response_structure='matches',
    )
    assert dbt_paas_data == gov_paas_data
    # expected_result = {
    #     'matches': [
    #         {'id': '1', 'match_id': None, 'similarity': '000000'},
    #     ]
    # }
    # print(data)
    # assert data == expected_result
