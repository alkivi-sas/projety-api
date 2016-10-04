"""Handles users endpoints."""
import logging

from flask import jsonify, abort

from ..auth import token_auth
from ..models import User, Acl
from . import api

logger = logging.getLogger(__name__)


@api.route('/v1.0/users/<user_id>/acls', methods=['GET'])
@token_auth.login_required
def get_acls(user_id):
    """
    Return list of ACLs.

    ---
    tags:
      - users
    security:
      - token: []
    parameters:
      - name: user_id
        in: path
        description: ID of user
        required: true
        type: integer
    responses:
      200:
        description: Returns a lists of acls
        schema:
          type: array
          items:
            $ref: '#/definitions/api_get_acl_get_ACL'
    """
    acls = User.query.get_or_404(user_id).acls
    return jsonify([acl.to_dict() for acl in acls])


@api.route('/v1.0/users/<user_id>/acls/<acl_id>', methods=['GET'])
@token_auth.login_required
def get_acl(user_id, acl_id):
    """
    Return an ACL.

    ---
    tags:
      - users
    security:
      - token: []
    parameters:
      - name: user_id
        in: path
        description: ID of user
        required: true
        type: integer
      - name: acl_id
        in: path
        description: ID of the ACL
        required: true
        type: integer
    responses:
      200:
        description: Returns a unique user
        schema:
          id: ACL
          required:
            - id
            - minions
            - functions
          properties:
            id:
              type: integer
              description: id of the acl
            minions:
              type: string
              description: minions allowed
            functions:
              type: string
              description: functions allowed
    """
    acl = Acl.query.get_or_404(acl_id)
    if int(acl.user_id) != int(user_id):
        abort(404)
    else:
        return jsonify(acl.to_dict())
