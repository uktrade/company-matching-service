import pytest
from flask import make_response
from mohawk import Sender
from mohawk.util import utc_now

from app.api.views import api, ac, json_error


@api.route('/test/', methods=["GET"])
@json_error
@ac.authentication_required
@ac.authorization_required
def mock_endpoint():
    return make_response('OK')


class CacheMock:
    cache = {}

    def set(self, key, value, ex):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key, None)


class TestAuthentication:
    @pytest.fixture(autouse=True)
    def setup(self, app):
        app.config['access_control'].update({
            'hawk_enabled': True,
            'hawk_nonce_enabled': True,
            'hawk_response_header': True,
            'hawk_algorithm': 'sha256',
            'hawk_accept_untrusted_content': False,
            'hawk_localtime_offset_in_seconds': 0,
            'hawk_timestamp_skew_in_seconds': 60,
            'issuers': [{
                'issuer': 'iss1',
                'key': 'secret1',
                'description': 'test user',
                'scope': '*'
            }],
        })
        app.cache = CacheMock()

    def test_successful_authentication(self, app):
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            sender.accept_response(
                response.headers.get('Server-Authorization'),
                content=response.get_data(),
                content_type=response.mimetype)
            assert response.status_code == 200
            assert response.get_data() == b'OK'

    def test_hawk_disabled(self, app):
        app.config['access_control']['hawk_enabled'] = False
        with app.test_client() as c:
            response = c.get('/test/')
            assert response.status_code == 200
            assert response.get_data() == b'OK'

    def test_wrong_key(self, app):
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'wrong_secret',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_invalid_id(self, app):
        sender = Sender(
            credentials={
                'id': 'invalid_id',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_missing_header(self, app):
        with app.test_client() as c:
            response = c.get('/test/')
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_expired_signature(self, app):
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
            _timestamp=str(utc_now(offset_in_seconds=-300))
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_once_only_request(self, app):
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_nonce_disabled(self, app):
        app.config['access_control']['hawk_nonce_enabled'] = False
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'

    def test_response_header(self, app):
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            app.config['access_control']['hawk_response_header'] = True
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.headers.get('Server-Authorization')

            app.config['access_control']['hawk_response_header'] = False
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert not response.headers.get('Server-Authorization')

    def test_invalid_config(self, app):
        app.config['access_control'].update({
            'issuers': [{
                'issuer': 'iss1',
                'description': 'test user',
                'scope': '*'
            }]
        })
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''


class TestAuthorization:
    @pytest.fixture(autouse=True)
    def setup(self, app):
        app.config['access_control'].update({
            'hawk_enabled': True,
            'hawk_nonce_enabled': False,
            'hawk_algorithm': 'sha256',
            'hawk_accept_untrusted_content': True,
            'hawk_localtime_offset_in_seconds': 0,
            'hawk_timestamp_skew_in_seconds': 60,
            'issuers': [
                {
                    'issuer': 'iss1',
                    'key': 'secret1',
                    'description': 'test user 1',
                    'scope': 'mock_endpoint'
                },
                {
                    'issuer': 'iss2',
                    'key': 'secret2',
                    'description': 'test user 2',
                    'scope': 'invalid_scope'
                },
                {
                    'issuer': 'iss3',
                    'key': 'secret3',
                    'description': 'test user 3',
                }
            ],
        })

    def test_successful_authorization(self, app):
        sender = Sender(
            credentials={
                'id': 'iss1',
                'key': 'secret1',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'

    def test_invalid_scope(self, app):
        sender = Sender(
            credentials={
                'id': 'iss2',
                'key': 'secret2',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_invalid_config(self, app):
        sender = Sender(
            credentials={
                'id': 'iss3',
                'key': 'secret3',
                'algorithm': 'sha256'
            },
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''
