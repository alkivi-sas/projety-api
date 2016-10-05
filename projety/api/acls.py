"""Handles users endpoints."""
import logging

from flask import jsonify, abort, request


from .. import db
from ..auth import token_auth
from ..models import User, Acl
from ..permissions import AclReadPermission, AclWritePermission
from ..exceptions import RoleError, ValidationError
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
      403:
        description: When forbidden by role
      404:
        description: When wrong user
    """
    permission = AclReadPermission(user_id)
    if not permission.can():
        raise RoleError(permission)

    acls = User.query.get_or_404(user_id).acls
    return jsonify([acl.to_dict() for acl in acls])


@api.route('/v1.0/users/<user_id>/acls', methods=['POST'])
@token_auth.login_required
def post_acl(user_id):
    """
    Create a new ACL.

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
      - name: acl_data
        in: body
        description: acl data
        required: true
        schema:
          id: acl_data
          properties:
            minions:
              description: Allowed minions
              type: string
            functions:
              description: Allowed functions
              type: string
    responses:
      200:
        description: Returns the new acl id
        schema:
          id: post_acl
          required:
            - id
          properties:
            id:
              type: integer
      403:
        description: When forbidden by role
      404:
        description: When wrong user
    """
    permission = AclWritePermission()
    if not permission.can():
        raise RoleError(permission)

    data = request.json
    creation_data = {'user_id': user_id}
    mandatory_keys = ['minions', 'functions']
    for key in mandatory_keys:
        if key not in data:
            raise ValidationError('Missing post data {0}'.format(key))
        else:
            creation_data[key] = data[key]

    # Now check if we already have an ACL
    acl = Acl.query.filter_by(**creation_data).first()
    if acl:
        raise ValidationError('ACL already exists : id {0}'.format(acl.id))

    acl = Acl(**creation_data)
    db.session.add(acl)
    db.session.commit()

    return jsonify({'id': acl.id})


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
            - user_id
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
            user_id:
              type: integer
              description: id of the user
      403:
        description: When forbidden by role
      404:
        description: When wrong user
    """
    permission = AclReadPermission(user_id)
    if not permission.can():
        raise RoleError(permission)

    acl = Acl.query.get_or_404(acl_id)
    if int(acl.user_id) != int(user_id):
        abort(404)
    else:
        return jsonify(acl.to_dict())


@api.route('/v1.0/users/<user_id>/acls/<acl_id>', methods=['PUT'])
@token_auth.login_required
def modify_acl(user_id, acl_id):
    """
    Modify an existing ACL.

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
      - name: acl_data
        in: body
        description: acl data
        required: true
        schema:
          $ref: '#/definitions/api_post_acl_post_acl_data'
    responses:
      200:
        description: When successfull
      403:
        description: When forbidden by role
      404:
        description: When wrong user or wrong acl
    """
    permission = AclWritePermission()
    if not permission.can():
        raise RoleError(permission)

    acl = Acl.query.get_or_404(acl_id)
    logger.warning(acl.to_dict())
    if int(acl.user_id) != int(user_id):
        abort(404)

    data = request.json
    changes = False
    mandatory_keys = ['minions', 'functions']
    for key in mandatory_keys:
        if key in data:
            if data[key] != getattr(acl, key):
                setattr(acl, key, data[key])
                changes = True

    if changes:
        db.session.add(acl)
        db.session.commit()

    return ''


@api.route('/v1.0/users/<user_id>/acls/<acl_id>', methods=['DELETE'])
@token_auth.login_required
def delete_acl(user_id, acl_id):
    """
    Delete an existing ACL.

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
        description: When successfull
      403:
        description: When forbidden by role
      404:
        description: When wrong user or wrong acl
    """
    permission = AclWritePermission()
    if not permission.can():
        raise RoleError(permission)

    acl = Acl.query.get_or_404(acl_id)
    logger.warning(acl.to_dict())
    if int(acl.user_id) != int(user_id):
        abort(404)

    db.session.delete(acl)
    db.session.commit()

    return ''
