"""Handles users endpoints."""

from flask import jsonify

from ..auth import token_auth
from ..models import User
from . import api


@api.route('/v1.0/users', methods=['GET'])
@token_auth.login_required
def get_users():
    """Return list of users."""
    users = User.query.order_by(User.updated_at.asc(), User.nickname.asc())
    return jsonify({'users': [user.to_dict() for user in users.all()]})


@api.route('/v1.0/users/<id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    """
    Return a user.

    This endpoint is publicly available, but if the client has a token it
    should send it, as that indicates to the server that the user is online.
    """
    return jsonify(User.query.get_or_404(id).to_dict())
