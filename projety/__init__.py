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
from celery import Celery

from config import config

# Flask extensions
db = SQLAlchemy()
cors = CORS()
celery = Celery(__name__,
                broker=os.environ.get('CELERY_BROKER_URL', 'redis://'),
                backend=os.environ.get('CELERY_BROKER_URL', 'redis://'))

# Import models so that they are registered with SQLAlchemy
from . import models  # noqa

# Import celery task so that it is registered with the Celery workers
from .api.tasks import run_flask_request  # noqa


def fix_logger(app):
    """Reset logging due to salt mess."""
    w_logger = logging.getLogger('werkzeug')
    logger = app.logger

    if app.debug:
        w_logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    del w_logger.handlers[:]
    del logger.handlers[:]


def create_app(config_name=None):
    """Return a flask app."""
    if config_name is None:
        config_name = os.environ.get('PROJETY_CONFIG', 'development')
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize flask extensions
    db.init_app(app)
    cors.init_app(app)
    celery.conf.update(config[config_name].CELERY_CONFIG)

    # Reset logging due to salt mess
    fix_logger(app)

    # Register API routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
