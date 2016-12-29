"""Manage the different configuration for the app."""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """Generic config object with default values."""

    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY',
                                '51f52814-0071-11e6-a247-000ec6c2372c')
    # App Settings
    AUTO_PING_SLEEP = 30
    CLEANING_SLEEP = 10

    # Extension CORS
    CORS_ORIGINS = '*'

    # Extension sqlalchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'db.sqlite'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Extension celery
    CELERY_CONFIG = {}

    # Extension socket.io
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('CELERY_BROKER_URL', 'redis://')

    # Extension websockify
    WEBSOCKET_MESSAGE_QUEUE = os.environ.get('CELERY_BROKER_URL', 'redis://')

    # Extension swagger
    SWAGGER = {'specs':
               [
                   {
                       'version': '1.0',
                       'title': 'Api v1.0',
                       'endpoint': 'api',
                       'description': 'This is the version 1 of our API',
                       'route': '/api/v1.0/spec',
                   },
               ],
               'securityDefinitions': {
                   'token': {
                       'type': 'apiKey',
                       'in': 'header',
                       'name': 'Authorization'
                   },
                   'basic': {
                       'type': 'basic'
                   }
               },
               'headers': [],
               }


class DevelopmentConfig(Config):
    """Specific for dev."""

    DEBUG = True


class ProductionConfig(Config):
    """Specific for prod."""

    pass


class TestingConfig(Config):
    """Specific for test."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    CELERY_CONFIG = {'CELERY_ALWAYS_EAGER': True}
    SOCKETIO_MESSAGE_QUEUE = None


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
