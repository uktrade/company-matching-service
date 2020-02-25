import logging
from functools import wraps

import redis
from flask import current_app as app, make_response, request
from flask import jsonify
from flask.blueprints import Blueprint
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

from app.algorithm import Matcher
from app.api.access_control import AccessControl
from app.api.schema import COMPANY_MATCH_BODY, COMPANY_UPDATE_BODY
from app.api.utils import get_verified_data
from app.db.models import HawkUsers

api = Blueprint(name="api", import_name=__name__)
ac = AccessControl()


@ac.client_key_loader
def get_client_key(client_id):
    client_key = HawkUsers.get_client_key(client_id)
    if client_key:
        return client_key
    else:
        raise LookupError()


@ac.client_scope_loader
def get_client_scope(client_id):
    client_scope = HawkUsers.get_client_scope(client_id)
    if client_scope:
        return client_scope
    else:
        raise LookupError()


@ac.nonce_checker
def seen_nonce(sender_id, nonce, timestamp):
    key = f'{sender_id}:{nonce}:{timestamp}'
    try:
        if app.cache.get(key):
            # We have already processed this nonce + timestamp.
            return True
        else:
            # Save this nonce + timestamp for later.
            app.cache.set(key, 'True', ex=300)
            return False
    except redis.exceptions.ConnectionError as e:
        logging.error(f'failed to connect to caching server: {str(e)}')
        return True


def json_error(f):
    @wraps(f)
    def error_handler(*args, **kwargs):
        try:
            response = f(*args, **kwargs)
        except NotFound:
            response = jsonify({})
            response.status_code = 404
        except BadRequest as e:
            response = jsonify({'error': e.description})
            response.status_code = 400
        except Unauthorized:
            response = make_response('')
            response.status_code = 401
        except Exception as e:
            logging.error(f'unexpected exception for API request: {str(e)}')
            response = make_response('')
            response.status_code = 500
            raise e
        return response

    return error_handler


@api.route('/healthcheck/', methods=["GET"])
def healthcheck():
    return jsonify({"status": "OK"})


@api.route('/api/v1/company/update/', methods=['POST'])
@json_error
@ac.authentication_required
@ac.authorization_required
def update():
    query = get_verified_data(request, COMPANY_UPDATE_BODY)
    match = request.args.get('match', 'true')
    if match not in ['true', 'false']:
        raise BadRequest('invalid match parameter. needs to be true or false')
    else:
        match = match == 'true'

    matcher = Matcher()
    matches = matcher.match(query['descriptions'], update=True, match=match)

    if match:
        result = {'matches': []}
        for row in matches:
            result['matches'].append({'id': row[0], 'match_id': row[1], 'similarity': row[2]})
        return jsonify(result)
    else:
        return '', 204


@api.route('/api/v1/company/match/', methods=['POST'])
@json_error
@ac.authentication_required
@ac.authorization_required
def match():
    query = get_verified_data(request, COMPANY_MATCH_BODY)
    result = {'matches': []}
    matcher = Matcher()
    matches = matcher.match(query['descriptions'], update=False)
    for row in matches:
        result['matches'].append({'id': row[0], 'match_id': row[1], 'similarity': row[2]})
    return jsonify(result)
