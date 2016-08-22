"""Module that manage authentification."""

from flask import jsonify, g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth

from . import db
from .models import User

# Authentication objects for username/password auth or a token auth
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')


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
        return False
    db.session.add(user)
    db.session.commit()
    g.current_user = user
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
        return False
    if user.token is None:
        # Revoke token
        return False
    db.session.add(user)
    db.session.commit()
    g.current_user = user
    return True
