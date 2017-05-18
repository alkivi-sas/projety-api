"""Middleware for websockify connection."""
import logging

logger = logging.getLogger(__name__)


class WsProxyMiddleware(object):
    """
    Route request to right app.

    Base on Engine.IO middleware.
    """

    def __init__(self, websockify_app, flask_app,
                 websockify_path='websockify'):
        """Init."""
        self.flask_app = flask_app
        self.websockify_app = websockify_app
        self.wsgi_app = flask_app.wsgi_app
        self.websockify_path = websockify_path

    def __call__(self, environ, start_response):
        """Wrap the call that dispatch request."""
        environ['flask.app'] = self.flask_app
        if 'gunicorn.socket' in environ:
            # gunicorn saves the socket under environ['gunicorn.socket'], while
            # eventlet saves it under environ['eventlet.input']. Eventlet also
            # stores the socket inside a wrapper class, while gunicon writes it
            # directly into the environment. To give eventlet's Websocket
            # module access to this socket when running under gunicorn, here we
            # copy the socket to the eventlet format.
            class Input(object):
                def __init__(self, socket):
                    self.socket = socket

                def get_socket(self):
                    return self.socket

            environ['eventlet.input'] = Input(environ['gunicorn.socket'])
        path = environ['PATH_INFO']
        if path is not None and \
                path.startswith('/{0}'.format(self.websockify_path)):
            return self.websockify_app.handle_request(environ, start_response)
        elif self.wsgi_app is not None:
            return self.wsgi_app(environ, start_response)
        else:
            start_response("404 Not Found", [('Content-type', 'text/plain')])
            return ['Not Found']
