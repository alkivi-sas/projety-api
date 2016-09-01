"""
Application factory.

Use to return a flask app configured.
"""
import os
import logging
logging.debug('init because of salt')


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
from flasgger import Swagger
from celery import Celery

from config import config

from flask_websockify import WebSockifyProxy

# Flask extensions
db = SQLAlchemy()
cors = CORS()
socketio = SocketIO()
wsproxy = WebSockifyProxy()
celery = Celery(__name__,
                broker=os.environ.get('CELERY_BROKER_URL', 'redis://'),
                backend=os.environ.get('CELERY_BROKER_URL', 'redis://'))
swagger = Swagger()

# Import models so that they are registered with SQLAlchemy
from . import models  # noqa

# Import celery task so that it is registered with the Celery workers
from .api.tasks import run_flask_request  # noqa

# Import Socket.IO events so that they are registered with Flask-SocketIO
from . import events  # noqa

# Import salt so they are ok+
from . import salt  # noqa


def fix_logger(app):
    """Reset logging due to salt mess."""
    w_logger = logging.getLogger('werkzeug')
    logger = app.logger

    if app.debug or app.testing:
        w_logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    del w_logger.handlers[:]
    del logger.handlers[:]


def create_app(config_name=None, main=True):
    """Return a flask app."""
    if config_name is None:
        config_name = os.environ.get('PROJETY_CONFIG', 'development')
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize flask extensions
    db.init_app(app)
    cors.init_app(app)
    swagger.init_app(app)
    wsproxy.init_app(app)
    if main:
        # Initialize socketio server and attach it to the message queue, so
        # that everything works even when there are multiple servers or
        # additional processes such as Celery workers wanting to access
        # Socket.IO
        socketio.init_app(app,
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    else:
        # Initialize socketio to emit events through through the message queue
        # Note that since Celery does not use eventlet, we have to be explicit
        # in setting the async mode to not use it.
        socketio.init_app(None,
                          message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'],
                          async_mode='threading')
    celery.conf.update(config[config_name].CELERY_CONFIG)

    # Reset logging due to salt mess
    fix_logger(app)

    # Register API routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Register handlers
    from .errors import not_found, method_not_supported, internal_server_error
    app.register_error_handler(404, not_found)
    app.register_error_handler(405, method_not_supported)
    app.register_error_handler(500, internal_server_error)

    return app
