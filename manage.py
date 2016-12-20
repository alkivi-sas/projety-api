#!/usr/bin/env python
"""
Script to manage the application.

It can be use to :
- start the dev server
- create the database
- seed the database
- test syntax with lint
- test the app with py.test
"""

import os
import subprocess
import sys
import random
import string

import eventlet
eventlet.monkey_patch()

from flask_script import Manager, Command, Server as _Server, Option


from projety import create_app, db, socketio
from projety.models import User, Acl, Role

manager = Manager(create_app)


def generate_password(length=15):
    """Helper to generate password for new users."""
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    random.seed = (os.urandom(1024))
    return ''.join(random.choice(chars) for i in range(length))


class Server(_Server):
    """Custom class to run server using socket.io."""

    help = description = 'Runs the Socket.IO web server'

    def get_options(self):
        """Parsing of options."""
        options = (
            Option('-h', '--host',
                   dest='host',
                   default=self.host),

            Option('-p', '--port',
                   dest='port',
                   type=int,
                   default=self.port),

            Option('-d', '--debug',
                   action='store_true',
                   dest='use_debugger',
                   help=('enable the Werkzeug debugger (DO NOT use in '
                         'production code)'),
                   default=self.use_debugger),
            Option('-D', '--no-debug',
                   action='store_false',
                   dest='use_debugger',
                   help='disable the Werkzeug debugger',
                   default=self.use_debugger),

            Option('-r', '--reload',
                   action='store_true',
                   dest='use_reloader',
                   help=('monitor Python files for changes (not 100%% safe '
                         'for production use)'),
                   default=self.use_reloader),
            Option('-R', '--no-reload',
                   action='store_false',
                   dest='use_reloader',
                   help='do not monitor Python files for changes',
                   default=self.use_reloader),
        )
        return options

    def __call__(self, app, host, port, use_debugger, use_reloader):
        """
        Custom caller for runserver.

        Override the default runserver command to start a Socket.IO server.
        """
        if use_debugger is None:
            use_debugger = app.debug
            if use_debugger is None:
                use_debugger = True
        if use_reloader is None:
            use_reloader = app.debug
        socketio.run(app,
                     host=host,
                     port=port,
                     debug=use_debugger,
                     use_reloader=use_reloader,
                     **self.server_options)


manager.add_command("runserver", Server())


class CeleryWorker(Command):
    """Starts the celery worker."""

    name = 'celery'
    capture_all_args = True

    def run(self, argv):
        """Execute celery."""
        ret = subprocess.call(
            # Temp patch only one worker
            # ['celery', 'worker', '-c', '1', '-A', 'projety.celery'] + argv)
            ['celery', 'worker', '-A', 'projety.celery'] + argv)
        sys.exit(ret)


manager.add_command("celery", CeleryWorker())


@manager.command
def createdb(drop_first=False):
    """Create the database."""
    if drop_first:
        db.drop_all()
    db.create_all()


@manager.command
def createacl(name, minions, functions):
    """Create an acl for a specific user."""
    user = User.query.filter_by(nickname=name).first()
    if not user:
        user = createuser(name)

    acl = Acl(minions=minions, functions=functions, user_id=user.id)
    db.session.add(acl)
    db.session.commit()
    print 'Acl for minion {0} with functions {1} created '.format(minions,
                                                                  functions) +\
          'for user {0}'.format(name)


@manager.command
def createrole(name, role):
    """Create a role for a specific user."""
    user = User.query.filter_by(nickname=name).first()
    if not user:
        user = createuser(name)

    r = Role(name=role, user_id=user.id)
    db.session.add(r)
    db.session.commit()
    print 'Role {0} created for user {1}'.format(role, name)


@manager.command
def createuser(name, expiration=3600):
    """Create a user and display its password and token."""
    user = User.query.filter_by(nickname=name).first()
    if user:
        print 'User {0} already exist'.format(name)
    else:
        password = generate_password()
        user = User(nickname=name, password=password)
        db.session.add(user)
        db.session.commit()

        print 'User {0} created with password {1}'.format(user.nickname,
                                                          password)

    token = user.generate_auth_token(expiration=expiration)
    print 'Here is a valid token : {0}'.format(token)
    return user


@manager.command
def resetuser(name):
    """Create a user and display its password and token."""
    user = User.query.filter_by(nickname=name).first()
    if user:
        print 'User {0} already exist'.format(name)

    password = generate_password()
    user.password = password
    db.session.add(user)
    db.session.commit()

    print 'User {0} created with password {1}'.format(user.nickname,
                                                      password)


@manager.command
def api_test():
    """Run unit tests."""
    from swagger_spec_validator import validate_spec_url
    test = validate_spec_url('http://127.0.0.1:5000/api/v1.0/spec')
    if not test:
        print 'Swagger DOC OK'


@manager.command
def test():
    """Run unit tests."""
    tests = subprocess.call(['python', '-c', 'import tests; tests.run()'])
    sys.exit(tests)


@manager.command
def lint():
    """Run code linter."""
    lint = subprocess.call(['flake8', '--ignore=E402', 'projety/',
                            'config.py', 'manage.py', 'tests/']) == 0
    if lint:
        print('OK')
    sys.exit(lint)


if __name__ == '__main__':
    if sys.argv[1] == 'test' or sys.argv[1] == 'lint':
        # small hack, to ensure that Flask-Script uses the testing
        # configuration if we are going to run the tests
        os.environ['FLACK_CONFIG'] = 'testing'
    manager.run()
