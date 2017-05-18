"""Handle tokens endpoints."""
import logging

from flask import jsonify, g, request

from ..exceptions import ValidationError
from ..auth import basic_auth
from . import api

logger = logging.getLogger(__name__)


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
    parameters:
      - name: expiration
        in: query
        description: Token expiration in seconds
        type: integer
        default: 600
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
    expiration = request.args.get('expiration', 600)
    try:
        expiration = int(expiration)
    except ValueError:
        raise ValidationError('expiration parameter is not an integer')

    token = g.current_user.generate_auth_token(expiration)
    return jsonify({'token': token})
