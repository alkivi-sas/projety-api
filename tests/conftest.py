"""
Configuration for pytest.

Define global fixture that are used during the tests.
"""
import pytest

from projety import create_app, socketio
from projety import db as _db
from projety.models import User, Acl


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
    u1 = User(nickname='admin', password='admin')
    u2 = User(nickname='restricted', password='restricted')
    _db.session.add_all([u1, u2])
    _db.session.commit()

    a1 = Acl(minions='.*', functions='.*', user_id=u1.id)
    a2 = Acl(minions='.*', functions='network.ip_addrs', user_id=u2.id)

    _db.session.add_all([a1, a2])
    _db.session.commit()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='session')
def client(app, db):
    """Session-wide client with app and db initialized."""
    return app.test_client()


@pytest.fixture
def app_class(app, request):
    """To have app."""
    if request.cls is not None:
        request.cls.app = app


@pytest.fixture
def socketio_client_class(app, request, db):
    """To have client socket.io."""
    if request.cls is not None:
        request.cls.socketio_client = socketio.test_client(app)
