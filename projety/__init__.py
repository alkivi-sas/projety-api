"""
Application factory.

Use to return a flask app configured.
"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import config

# Flask extensions
db = SQLAlchemy()

# Import models so that they are registered with SQLAlchemy
from . import models  # noqa


def create_app(config_name=None):
    """Return a flask app."""
    if config_name is None:
        config_name = os.environ.get('PROJETY_CONFIG', 'development')
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize flask extensions
    db.init_app(app)

    # Register API routes
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
