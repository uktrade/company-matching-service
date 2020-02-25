import json


def assert_search_api_response(
    app_context, api, body, expected_response, params='', order_matters=False
):
    status_code, data = _post_request(params, api, body, app_context)
    assert status_code == expected_response[0]
    assert _ordered(data) == _ordered(expected_response[1])
    if order_matters:
        for i, record in enumerate(data['result']):
            # check if records are in same order
            assert _ordered(record) == _ordered(expected_response[1]['result'][i])


def _post_request(params, endpoint, json_query, app_context):
    url = f'{endpoint}?{params}'

    res = app_context.post(url, data=json.dumps(json_query), content_type='application/json',)
    status_code = res.status_code
    try:
        data = json.loads(res.get_data())
    except ValueError:
        # This can happen when an unexpected response is returned,
        # for example if the backend hits an error.
        # Handling this situation here makes it a bit clearer what is
        # going on when the test fails.
        data = None
    return status_code, data


def _ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, _ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(_ordered(x) for x in obj)
    else:
        return obj
