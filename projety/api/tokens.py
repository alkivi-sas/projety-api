"""Handle tokens endpoints."""

from flask import jsonify, g

from .. import db
from ..auth import basic_auth, token_auth
from . import api


@api.route('/v1.0/tokens', methods=['POST'])
@basic_auth.login_required
def new_token():
    """
    Request a user token.

    This endpoint requires HTTP Basic authentication with nickname and
    password.
    ---
    tags:
      - tokens
    security:
      - basic: []
    responses:
      200:
        description: Returns a valid token
        schema:
          id: Token
          required:
            - token
          properties:
            token:
              type: string
              description: A valid token for the user
    """
    if g.current_user.token is None:
        g.current_user.generate_token()
        db.session.add(g.current_user)
        db.session.commit()
    return jsonify({'token': g.current_user.token})


@api.route('/v1.0/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    """
    Revoke a user token.

    This endpoint requires bearer authentication using a valid token.
    ---
    tags:
      - tokens
    security:
      - token: []
    responses:
      204:
        description: Token is deleted
    """
    g.current_user.token = None
    db.session.add(g.current_user)
    db.session.commit()
    return '', 204
