import json

from jsonschema import validate, FormatChecker
from jsonschema.exceptions import ValidationError
from werkzeug.exceptions import BadRequest


def get_verified_data(request, schema):
    """
    :param
        request: request object
        schema: json schema to validate against

    :return: dict
        data is verified against a JSON schema and errors are raised accordingly
        data is decoded from JSON to a dict and returned
    """
    try:
        data = json.loads(request.data.decode('utf-8'))
    except ValueError:
        raise BadRequest("Unable to read JSON payload")
    try:
        validate(data, schema, format_checker=FormatChecker())
    except ValidationError as e:
        xcpt = BadRequest(e.message)
        xcpt.data = {"source": {"path": schema_validation_error_path(e)}}
        raise xcpt
    return data


def schema_validation_error_path(e):
    """
    :param e: a Schema ValidationError instance
    :return: string
    builds a source/pointer from a JsonSchema SchemaValidationError instance
    for use in an API error response, as defined:
    http://jsonapi.org/format/#errors
    """
    path = ""
    while len(e.path) > 0:
        path += "/{}".format(e.path.popleft())
    return path or "/"


