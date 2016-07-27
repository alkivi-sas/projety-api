"""Handles users endpoints."""

from flask import jsonify

from ..auth import token_auth
from ..models import User
from . import api


@api.route('/v1.0/users', methods=['GET'])
@token_auth.login_required
def get_users():
    """
    Return list of users.

    ---
    tags:
      - users
    security:
      - token: []
    responses:
      200:
        description: Returns a lists of users
        schema:
          type: array
          items:
            $ref: '#/definitions/api_get_user_get_User'
    """
    users = User.query.order_by(User.updated_at.asc(), User.nickname.asc())
    return jsonify([user.to_dict() for user in users.all()])


@api.route('/v1.0/users/<id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    """
    Return a user.

    ---
    tags:
      - users
    security:
      - token: []
    parameters:
      - name: id
        in: path
        description: ID of user
        required: true
        type: integer
    responses:
      200:
        description: Returns a unique user
        schema:
          id: User
          required:
            - id
            - nickname
          properties:
            id:
              type: integer
              description: id of the user
            nickname:
              type: string
              description: name for user
            created_at:
              type: string
              format: date-time
              description: date of creation
            updated_at:
              type: string
              format: date-time
              description: date of creation
            last_seen_at:
              type: string
              format: date-time
              description: date of creation
    """
    return jsonify(User.query.get_or_404(id).to_dict())
