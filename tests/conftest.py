"""
Configuration for pytest.

Define global fixture that are used during the tests.
"""
import pytest

from projety import create_app
from projety import db as _db
from projety.models import User


@pytest.fixture(scope='session')
def app(request):
    """Session-wide test application."""
    app = create_app('testing')

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='session')
def db(app, request):
    """Session-wide test database."""
    def teardown():
        _db.drop_all()

    _db.app = app

    _db.drop_all()  # just in case
    _db.create_all()
    u = User(nickname='alkivi', password='alkivi123')
    _db.session.add_all([u])
    _db.session.commit()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='session')
def client(app, db):
    """Session-wide client with app and db initialized."""
    return app.test_client()
