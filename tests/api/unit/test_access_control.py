import pytest
from flask import make_response
from mohawk import Sender
from mohawk.util import utc_now

from app.api.views import ac, api, json_error
from app.db.models import HawkUsers


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
    def setup(self, app_with_db):
        app_with_db.cache = CacheMock()
        app_with_db.config['access_control'].update(
            {
                'hawk_enabled': True,
                'hawk_nonce_enabled': True,
                'hawk_response_header': True,
                'hawk_algorithm': 'sha256',
                'hawk_accept_untrusted_content': False,
                'hawk_localtime_offset_in_seconds': 0,
                'hawk_timestamp_skew_in_seconds': 60,
            }
        )
        self.app = app_with_db
        self.client_id = 'iss1'
        self.client_key = 'secret1'
        self.client_scope = ['*']
        self.description = 'test authentication'
        HawkUsers.add_user(
            client_id=self.client_id,
            client_key=self.client_key,
            client_scope=self.client_scope,
            description=self.description,
        )

    def test_successful_authentication(self):
        sender = Sender(
            credentials={'id': self.client_id, 'key': self.client_key, 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with self.app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'
            # check if accepted response doesn't throw exception
            sender.accept_response(
                response.headers.get('Server-Authorization'),
                content=response.get_data(),
                content_type=response.mimetype,
            )

    def test_hawk_disabled(self):
        self.app.config['access_control']['hawk_enabled'] = False
        with self.app.test_client() as c:
            response = c.get('/test/')
            assert response.status_code == 200
            assert response.get_data() == b'OK'

    def test_wrong_key(self):
        sender = Sender(
            credentials={'id': 'iss1', 'key': 'wrong_secret', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with self.app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_invalid_id(self):
        sender = Sender(
            credentials={'id': 'invalid_id', 'key': 'secret1', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with self.app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_missing_header(self):
        with self.app.test_client() as c:
            response = c.get('/test/')
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_expired_signature(self):
        sender = Sender(
            credentials={'id': 'iss1', 'key': 'secret1', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
            _timestamp=str(utc_now(offset_in_seconds=-300)),
        )
        with self.app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_once_only_request(self):
        sender = Sender(
            credentials={'id': 'iss1', 'key': 'secret1', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with self.app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_nonce_disabled(self):
        self.app.config['access_control']['hawk_nonce_enabled'] = False
        sender = Sender(
            credentials={'id': 'iss1', 'key': 'secret1', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with self.app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'

    def test_response_header(self):
        sender = Sender(
            credentials={'id': 'iss1', 'key': 'secret1', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with self.app.test_client() as c:
            self.app.config['access_control']['hawk_response_header'] = True
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.headers.get('Server-Authorization')

            self.app.config['access_control']['hawk_response_header'] = False
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert not response.headers.get('Server-Authorization')

    def test_endpoints_secured(self):
        urls = [
            '/api/v1/company/match/',
            '/api/v1/company/update/',
        ]
        with self.app.test_client() as c:
            for url in urls:
                response = c.post(url)
                assert response.status_code == 401


class TestAuthorization:
    @pytest.fixture(autouse=True)
    def setup(self, app_with_db):
        app_with_db.config['access_control'].update(
            {
                'hawk_enabled': True,
                'hawk_nonce_enabled': False,
                'hawk_algorithm': 'sha256',
                'hawk_accept_untrusted_content': True,
                'hawk_localtime_offset_in_seconds': 0,
                'hawk_timestamp_skew_in_seconds': 60,
            }
        )
        self.client_id = 'iss1'
        self.client_key = 'secret1'
        self.client_scope = ['*']
        HawkUsers.add_user(
            client_id='iss1',
            client_key='secret1',
            client_scope=['mock_endpoint'],
            description='test authorization 1',
        )
        HawkUsers.add_user(
            client_id='iss2',
            client_key='secret2',
            client_scope=['invalid_scope'],
            description='test authorization 2',
        )
        HawkUsers.add_user(
            client_id='iss3',
            client_key='secret3',
            client_scope=['other_endpoint', 'mock_endpoint'],
            description='test authorization 3',
        )
        self.app = app_with_db

    def test_successful_authorization(self, app):
        sender = Sender(
            credentials={'id': 'iss1', 'key': 'secret1', 'algorithm': 'sha256'},
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
            credentials={'id': 'iss2', 'key': 'secret2', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 401
            assert response.get_data() == b''

    def test_multiple_scopes(self, app):
        sender = Sender(
            credentials={'id': 'iss3', 'key': 'secret3', 'algorithm': 'sha256'},
            url='http://localhost:80/test/',
            method='GET',
            content='',
            content_type='',
        )
        with app.test_client() as c:
            response = c.get('/test/', headers={'Authorization': sender.request_header})
            assert response.status_code == 200
            assert response.get_data() == b'OK'
