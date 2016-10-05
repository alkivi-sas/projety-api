"""Module that manage authentification."""
import logging

from flask import jsonify, g, current_app
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask_principal import (Identity, AnonymousIdentity,
                             UserNeed, RoleNeed,
                             identity_changed)

from . import db
from .models import User

# Authentication objects for username/password auth or a token auth
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')

logger = logging.getLogger(__name__)


def update_user(user=None):
    """
    Install the user as current user of the app.

    Setup the g.current_user variable.
    Add the user to the session.
    Update Flask-Principal.

    If no user, install AnonymousIdentity
    """
    if user:
        db.session.add(user)
        db.session.commit()
        g.current_user = user

        # Tell Flask-Principal the identity changed
        identity = Identity(user.id)
        identity.user = user

        # By default we can self need
        identity.provides.add(UserNeed(user.id))

        # Add roles
        for role in user.roles:
            identity.provides.add(RoleNeed(role.name))

        identity_changed.send(current_app._get_current_object(),
                              identity=identity)
    else:
        # Tell Flask-Principal the user is anonymous
        identity_changed.send(current_app._get_current_object(),
                              identity=AnonymousIdentity())


@basic_auth.verify_password
def verify_password(nickname, password):
    """
    Password verification callback.

    ---
    securityDefinitions:
      UserSecurity:
        type: basic
    """
    user = User.query.filter_by(nickname=nickname).first()
    if user is None or not user.verify_password(password):
        update_user()
        return False
    else:
        update_user(user)
        return True


@token_auth.error_handler
@basic_auth.error_handler
def auth_error():
    """Return a 401 error to the client."""
    # To avoid login prompts in the browser, use the "Bearer" realm.
    message = {'status': 401, 'error': 'authentication required'}
    return (jsonify(message), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})


@token_auth.verify_token
def verify_token(token):
    """
    Token verification callback.

    ---
    securityDefinitions:
      UserSecurity:
        type: apiKey
        in: header
        name: token
    """
    user = User.verify_auth_token(token)
    if user is None:
        update_user()
        return False
    else:
        update_user(user)
        return True
