"""Handle proxying of request."""
import importlib
import logging
import uuid

from six.moves import urllib

from .socket import ProxySocket
from .tokens import TokenManager

logger = logging.getLogger(__name__)


class WsProxy(object):
    """
    Websockify proxy.

    Catch a GET request on a specific path.
    Extract port from it.
    Then use a socket and proxy data back and forth

    :param async_mode: The asynchronous model to use. See the Deployment
                       section in the documentation for a description of the
                       available options. Valid async modes are "threading",
                       "eventlet", "gevent" and "gevent_uwsgi". If this
                       argument is not given, "eventlet" is tried first, then
                       "gevent_uwsgi", then "gevent", and finally "threading".
                       The first async mode that has all its dependencies
                       installed is then one that is chosen.
    :param cookie: Name of the HTTP cookie that contains the client session
                   id. If set to ``None``, a cookie is not sent to the client.
    :param cors_allowed_origins: List of origins that are allowed to connect
                                 to this server. All origins are allowed by
                                 default.
    :param cors_credentials: Whether credentials (cookies, authentication) are
                             allowed in requests to this server.
    :param kwargs: Reserved for future extensions, any additional parameters
                   given as keyword arguments will be silently ignored.
    """

    def __init__(self, async_mode=None,
                 cookie='websockify', cors_allowed_origins=None,
                 cors_credentials=True, **kwargs):
        """Init."""
        self.cookie = cookie
        self.cors_allowed_origins = cors_allowed_origins
        self.cors_credentials = cors_credentials
        self.sockets = {}
        self.environ = {}
        self.token_manager = TokenManager()

        # Default mode for async
        if async_mode is None:
            modes = ['eventlet', 'gevent_uwsgi', 'gevent', 'threading']
        else:
            modes = [async_mode]

        self.async = None
        self.async_mode = None
        for mode in modes:
            try:
                self.async = importlib.import_module(
                    'engineio.async_' + mode).async
                self.async_mode = mode
                break
            except ImportError:
                pass
        if self.async_mode is None:
            raise ValueError('Invalid async_mode specified')

        logger.info('Server initialized for %s.', self.async_mode)

    def create_token(self, minion, expiration=3600):
        """Create a token to use in no_vnc."""
        return self.token_manager.create_token(minion, expiration)

    def get_token(self, minion):
        """Return a valid token if it exist for a minion."""
        return self.token_manager.get_minion_token(minion)

    def delete_token(self, token):
        """Delete a token to use in no_vnc."""
        return self.token_manager.delete_token(token)

    def _test_websocket(self, environ):
        """Test environ for websocket upgrade."""
        http_upgrade = ''
        if 'HTTP_UPGRADE' in environ:
            http_upgrade = environ['HTTP_UPGRADE'].lower()

        return http_upgrade == 'websocket'

    def _get_websockify_port(self, environ):
        """Test path."""
        path = environ['PATH_INFO']
        port = path.split('/')[2]
        try:
            port = int(port)
        except:
            return False
        return port

    def handle_request(self, environ, start_response):
        """Handle an HTTP request from the client.

        This is the entry point of the Engine.IO application, using the same
        interface as a WSGI application. For the typical usage, this function
        is invoked by the :class:`Middleware` instance, but it can be invoked
        directly when the middleware is not used.

        :param environ: The WSGI environment.
        :param start_response: The WSGI ``start_response`` function.

        This function returns the HTTP response body to deliver to the client
        as a byte sequence.
        """
        # First upgrade a connection to websocket
        if not self._test_websocket(environ):
            r = self._bad_request('Not a websocket request')
            return self._respond(environ, start_response, r)

        # Create sid for new connection
        sid = self._generate_id()

        # Generate new socket
        s = ProxySocket(self, sid)
        self.sockets[sid] = s

        # Auth stuff
        if not self.validate_connection(environ, sid):
            r = self._bad_request('Unable to validate connection')
            return self._respond(environ, start_response, r)

        # Handle handshake
        if not s.do_websocket_handshake(environ, start_response):
            r = self._bad_request('Unable to perform handshake')
            return self._respond(environ, start_response, r)

        # Now handle web_socket_client
        return s.do_proxy(environ, start_response)

    def start_background_task(self, target, *args, **kwargs):
        """Start a background task using the appropriate async model.

        This is a utility function that applications can use to start a
        background task using the method that is compatible with the
        selected async mode.

        :param target: the target function to execute.
        :param args: arguments to pass to the function.
        :param kwargs: keyword arguments to pass to the function.

        This function returns an object compatible with the `Thread` class in
        the Python standard library. The `start()` method on this object is
        already called by this function.
        """
        th = getattr(self.async['threading'],
                     self.async['thread_class'])(target=target, args=args,
                                                 kwargs=kwargs)
        th.start()
        return th  # pragma: no cover

    def _generate_id(self):
        """Generate a unique session id."""
        return uuid.uuid4().hex

    def validate_connection(self, environ, sid):
        """Check that the token is valid."""
        # Parse url
        query = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
        if 'token' not in query:
            return False

        # Validate token
        token = query['token'][0]
        data = self.token_manager.get_token(token)
        if not data:
            return False

        # Push port into socket
        socket = self.sockets[sid]
        if not socket:
            return False
        socket.setup_proxy(data.port)

        return True

    def _bad_request(self, message):
        """Generate a bad request HTTP error response."""
        return {'status': '400 BAD REQUEST',
                'headers': [('Content-Type', 'text/plain')],
                'response': b'{0}'.format(message)}

    def _respond(self, environ, start_response, r):
        """Send a request back."""
        cors_headers = self._cors_headers(environ)
        start_response(r['status'], r['headers'] + cors_headers)
        return [r['response']]

    def _cors_headers(self, environ):
        """Return the cross-origin-resource-sharing headers."""
        if self.cors_allowed_origins is not None and \
                environ.get('HTTP_ORIGIN', '') not in \
                self.cors_allowed_origins:
            return []
        if 'HTTP_ORIGIN' in environ:
            headers = [('Access-Control-Allow-Origin', environ['HTTP_ORIGIN'])]
        else:
            headers = [('Access-Control-Allow-Origin', '*')]
        if self.cors_credentials:
            headers += [('Access-Control-Allow-Credentials', 'true')]
        return headers
