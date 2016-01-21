import websockets

from importlib import import_module
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.utils.functional import SimpleLazyObject


class FakeRequest(object):
    def __init__(self, path, session_key):
        from django.contrib.auth.middleware import get_user

        self.session_key = session_key

        self.path = path
        self.user = SimpleLazyObject(lambda: get_user(self))

    @property
    def session(self):
        if not hasattr(self, '_session'):
            engine = import_module(settings.SESSION_ENGINE)

            setattr(self, '_session', engine.SessionStore(self.session_key))

        return getattr(self, '_session')


class RequestServerProtocol(websockets.server.WebSocketServerProtocol):
    """ WebSocketServerProtocol that gives handler a request-like
        object which might contain the session/user if token was provided.
    """

    TOKEN_PARAM = 'token'

    def get_handler_kwargs(self, path, get_header):
        query_dict = parse_qs(urlparse(path).query)

        session_key = query_dict.get(getattr(settings, 'TG_PUBSUB_TOKEN_PARAM', self.TOKEN_PARAM), [''])[0]

        # Construct a request
        request = FakeRequest(path, session_key)

        return {
            'request': request,
        }


class SessionRequiredServerProtocol(RequestServerProtocol):
    """ WebSocketServerProtocol which only allows handshakes with a valid token
    """

    def get_handler_kwargs(self, path, get_header):
        handler_kwargs = super().get_handler_kwargs(path, get_header)

        # If no token provided, stop the handshake.
        if not handler_kwargs['request'].session_key:
            raise websockets.InvalidOrigin('Permission denied')

        return handler_kwargs


class AnyUserServerProtocol(SessionRequiredServerProtocol):
    """ WebSocketServerProtocol implementation that allows any users (that provide a token)
    """

    def has_permissions(self, request):
        return request is not None

    def get_handler_kwargs(self, path, get_header):
        handler_kwargs = super().get_handler_kwargs(path, get_header)

        if not self.has_permissions(handler_kwargs['request']):
            raise websockets.InvalidOrigin('Permission denied')

        return handler_kwargs


class AnonymousUserServerProtocol(AnyUserServerProtocol):
    """ WebSocketServerProtocol implementation that only allows anonymous users
    """

    def has_permissions(self, request):
        if super().has_permissions(request):
            return request.user.is_anonymous()

        return False


class AuthenticatedUserServerProtocol(AnyUserServerProtocol):
    """ WebSocketServerProtocol implementation that only allows authenticated users
    """

    def has_permissions(self, request):
        if super().has_permissions(request):
            return request.user.is_authenticated()

        return False


class StaffUserServerProtocol(AuthenticatedUserServerProtocol):
    """ WebSocketServerProtocol implementation that only allows staff users
    """

    def has_permissions(self, request):
        if super().has_permissions(request):
            return request.user.is_staff() or request.user.is_superuser()

        return False


class SuperUserServerProtocol(StaffUserServerProtocol):
    """ WebSocketServerProtocol implementation that only allows superusers
    """

    def has_permissions(self, request):
        if super().has_permissions(request):
            return request.user.is_superuser()

        return False
