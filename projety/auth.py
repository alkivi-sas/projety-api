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
    """Password verification callback."""
    user = User.query.filter_by(nickname=nickname).first()
    if user is None or not user.verify_password(password):
        return False
    db.session.add(user)
    db.session.commit()
    g.current_user = user
    return True


@basic_auth.error_handler
def password_error():
    """Return a 401 error to the client."""
    # To avoid login prompts in the browser, use the "Bearer" realm.
    return (jsonify({'error': 'authentication required'}), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})


@token_auth.verify_token
def verify_token(token):
    """Token verification callback."""
    user = User.query.filter_by(token=token).first()
    if user is None:
        return False
    db.session.add(user)
    db.session.commit()
    g.current_user = user
    return True


@token_auth.error_handler
def token_error():
    """Return a 401 error to the client."""
    return (jsonify({'error': 'authentication required'}), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})
