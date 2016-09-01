"""Flask extension for handling our proxy request."""
import logging

from .server import WebSockifyServer
from .middleware import WebSockifyProxyMiddleware

logger = logging.getLogger(__name__)


class WebSockifyProxy(object):
    """
    Create a Flask-WebSockify server.

    :param app: The flask application instance. If the application instance
                isn't known at the time this class is instantiated, then call
                ``websockify.init_app(app)`` once the application instance is
                available.
    :param path: The path where the WebSockify server is exposed. Defaults to
                 ``'websockify'``. Leave this as is unless you know what you
                 are doing.
    :param resource: Alias to ``path``.
    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``.
    """

    def __init__(self, app=None, **kwargs):
        """Init."""
        self.server = None
        self.server_options = None
        self.wsgi_server = None
        self.handlers = []
        self.exception_handlers = {}
        self.default_exception_handler = None
        if app is not None or len(kwargs) > 0:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        """For later init in flask."""
        if app is not None:
            if not hasattr(app, 'extensions'):
                app.extensions = {}  # pragma: no cover
            app.extensions['websockify'] = self

        resource = kwargs.pop('path', kwargs.pop('resource', 'websockify'))
        if resource.startswith('/'):
            resource = resource[1:]

        self.server = WebSockifyServer(logger=logger)
        if app is not None:
            # here we attach the WebSockify middlware to the WebSockifyProxy
            # object so it can be referenced later if debug middleware needs
            # to be inserted
            self.websockify_mw = WebSockifyProxyMiddleware(
                self.server, app,
                websockify_path=resource)
            app.wsgi_app = self.websockify_mw
