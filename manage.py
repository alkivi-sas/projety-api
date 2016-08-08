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

import subprocess
import sys

from flask_script import Manager

from projety import create_app, db
from projety.models import User

manager = Manager(create_app)


@manager.command
def createdb(drop_first=False):
    """Create the database."""
    if drop_first:
        db.drop_all()
    db.create_all()

    user_to_add = []
    for user in ['anthony', 'luc', 'ronan']:
        test = User.query.filter_by(nickname=user).first()
        if not test:
            to_add = User(nickname=user, password='alkivi123')
            user_to_add.append(to_add)

    if user_to_add:
        db.session.add_all(user_to_add)
        db.session.commit()


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
    manager.run()
