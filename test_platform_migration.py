import os
import json
import requests
from mohawk import Sender

# MATCHING_SERVICE_BASE_URL = os.environ.get("MATCHING_SERVICE_BASE_URL")
MATCHING_SERVICE_BASE_URL = "http://localhost:5080"
HAWK_CLIENT_ID = os.environ.get("HAWK_CLIENT_ID", "weird")
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
    descriptions = []
    request = {'descriptions': descriptions}
    match_type = "match"
    data = _hawk_api_request(
        url=f'{MATCHING_SERVICE_BASE_URL}/api/v1/company/{match_type}/',
        method='POST',
        query=request,
        credentials=HAWK_CREDENTIALS,
        expected_response_structure='matches',
    )
    print(data)
