# coding: utf-8
"""
This module provides API access control based on Hawk scheme

"""
from functools import wraps

from flask import current_app, request
from mohawk.util import parse_authorization_header
from werkzeug.exceptions import BadRequest, Unauthorized

try:
    import mohawk
except ImportError:
    pass

__all__ = ('AccessControl',)


class AccessControl:
    def __init__(self):
        self._client_key_loader_func = None
        self._nonce_checker_func = None
        self._client_scope_loader_func = None

    def client_key_loader(self, f):
        """ Function to be called to find a client key.

        :param f: The callback for retrieving a client key.

        """

        @wraps(f)
        def wrapped_f(client_id):
            client_key = f(client_id)
            return {
                'id': client_id,
                'key': client_key,
                'algorithm': current_app.config['access_control']['hawk_algorithm'],
            }

        self._client_key_loader_func = wrapped_f
        return wrapped_f

    def nonce_checker(self, f):
        """ Registers a function to be called to check a nonce.

        Function you set has to take a sender_id, nonce, timestamp and return a bool::

        :param f: The callback for checking a nonce.

        """

        @wraps(f)
        def wrapped_f(sender_id, nonce, timestamp):
            return f(sender_id, nonce, timestamp)

        self._nonce_checker_func = wrapped_f
        return wrapped_f

    def authentication_required(self, view_func):
        """ Decorator that provides an access to view function for
        authenticated users only.
        """

        @wraps(view_func)
        def wrapped_view_func(*args, **kwargs):
            hawk_enabled = current_app.config['access_control']['hawk_enabled']
            hawk_response_header = current_app.config['access_control']['hawk_response_header']

            if hawk_enabled:
                receiver = self._auth_by_signature()
            response = view_func(*args, **kwargs)
            if hawk_enabled and hawk_response_header:
                response.headers['Server-Authorization'] = receiver.respond(
                    content=response.get_data(), content_type=response.mimetype
                )
            return response

        return wrapped_view_func

    def _auth_by_signature(self):
        if self._client_key_loader_func is None:
            raise RuntimeError('Client key loader function was not defined')
        if 'Authorization' not in request.headers:
            raise Unauthorized()

        try:
            return mohawk.Receiver(
                credentials_map=self._client_key_loader_func,
                seen_nonce=self._nonce_checker_func
                if current_app.config['access_control']['hawk_nonce_enabled']
                else None,
                request_header=request.headers['Authorization'],
                url=request.url,
                method=request.method,
                content=request.get_data(),
                content_type=request.mimetype,
                accept_untrusted_content=current_app.config['access_control'][
                    'hawk_accept_untrusted_content'
                ],
                localtime_offset_in_seconds=current_app.config['access_control'][
                    'hawk_localtime_offset_in_seconds'
                ],
                timestamp_skew_in_seconds=current_app.config['access_control'][
                    'hawk_timestamp_skew_in_seconds'
                ],
            )
        except mohawk.exc.MacMismatch:
            raise Unauthorized()
        except (
            mohawk.exc.CredentialsLookupError,
            mohawk.exc.AlreadyProcessed,
            mohawk.exc.MisComputedContentHash,
            mohawk.exc.TokenExpired,
        ) as e:
            raise Unauthorized(str(e))
        except mohawk.exc.HawkFail as e:
            raise BadRequest(str(e))
        except KeyError:
            raise BadRequest()

    def client_scope_loader(self, f):
        """ Function to be called to find a client scope.

        :param f: The callback for retrieving a client scope.

        """

        @wraps(f)
        def wrapped_f(client_id):
            client_scope = f(client_id)
            return client_scope

        self._client_scope_loader_func = wrapped_f
        return wrapped_f

    def authorization_required(self, view_func):
        """ Decorator that provides access to view function for authorized users only.
        i.e the endpoint needs to be part of the issuer access scope.
        """

        @wraps(view_func)
        def handler(*args, **kwargs):
            if current_app.config['access_control']['hawk_enabled']:
                if self._client_scope_loader_func is None:
                    raise RuntimeError('Client scope loader function was not defined')
                try:
                    authorization_header = request.headers['Authorization']
                    attributes = parse_authorization_header(authorization_header)
                    id = attributes['id']
                except AttributeError or KeyError:
                    raise Unauthorized('Invalid authorization header.')
                scopes = self._client_scope_loader_func(id)
                if '*' in scopes or view_func.__name__ in scopes:
                    return view_func(*args, **kwargs)
                raise Unauthorized('Invalid authorization scope.')
            else:
                return view_func(*args, **kwargs)

        return handler
