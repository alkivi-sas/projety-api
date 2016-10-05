"""Handles users endpoints."""
import logging

from flask import jsonify, abort, request

from .. import db
from ..auth import token_auth
from ..models import User, Role
from ..permissions import RoleReadPermission, RoleWritePermission
from ..exceptions import RoleError, ValidationError
from . import api

logger = logging.getLogger(__name__)


@api.route('/v1.0/users/<user_id>/roles', methods=['GET'])
@token_auth.login_required
def get_roles(user_id):
    """
    Return list of Roles.

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
        description: Returns a lists of roles
        schema:
          type: array
          items:
            $ref: '#/definitions/api_get_role_get_Role'
      403:
        description: When forbidden by role
      404:
        description: When wrong user
    """
    permission = RoleReadPermission(user_id)
    if not permission.can():
        raise RoleError(permission)

    roles = User.query.get_or_404(user_id).roles
    return jsonify([role.to_dict() for role in roles])


@api.route('/v1.0/users/<user_id>/roles', methods=['POST'])
@token_auth.login_required
def post_role(user_id):
    """
    Create a new Role.

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
      - name: role_data
        in: body
        description: role data
        required: true
        schema:
          id: role_data
          properties:
            name:
              description: Name of the role
              type: string
    responses:
      200:
        description: Returns the new role id
        schema:
          id: post_role
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
    permission = RoleWritePermission()
    if not permission.can():
        raise RoleError(permission)

    data = request.json
    creation_data = {'user_id': user_id}
    mandatory_keys = ['name']
    for key in mandatory_keys:
        if key not in data:
            raise ValidationError('Missing post data {0}'.format(key))
        else:
            creation_data[key] = data[key]

    # Now check if we already have an Role
    role = Role.query.filter_by(**creation_data).first()
    if role:
        raise ValidationError('Role already exists : id {0}'.format(role.id))

    role = Role(**creation_data)
    db.session.add(role)
    db.session.commit()

    return jsonify({'id': role.id})


@api.route('/v1.0/users/<user_id>/roles/<role_id>', methods=['GET'])
@token_auth.login_required
def get_role(user_id, role_id):
    """
    Return an Role.

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
      - name: role_id
        in: path
        description: ID of the Role
        required: true
        type: integer
    responses:
      200:
        description: Returns a unique role
        schema:
          id: Role
          required:
            - id
            - name
            - user_id
          properties:
            id:
              type: integer
              description: id of the role
            name:
              type: string
              description: name of the role
            user_id:
              type: integer
              description: id of the user
      403:
        description: When forbidden by role
      404:
        description: When wrong user
    """
    permission = RoleReadPermission(user_id)
    if not permission.can():
        raise RoleError(permission)

    role = Role.query.get_or_404(role_id)
    if int(role.user_id) != int(user_id):
        abort(404)
    else:
        return jsonify(role.to_dict())


@api.route('/v1.0/users/<user_id>/roles/<role_id>', methods=['PUT'])
@token_auth.login_required
def modify_role(user_id, role_id):
    """
    Modify an existing Role.

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
      - name: role_id
        in: path
        description: ID of the Role
        required: true
        type: integer
      - name: role_data
        in: body
        description: role data
        required: true
        schema:
          $ref: '#/definitions/api_post_role_post_role_data'
    responses:
      200:
        description: When successfull
      403:
        description: When forbidden by role
      404:
        description: When wrong user or wrong role
    """
    permission = RoleWritePermission()
    if not permission.can():
        raise RoleError(permission)

    role = Role.query.get_or_404(role_id)
    logger.warning(role.to_dict())
    if int(role.user_id) != int(user_id):
        abort(404)

    data = request.json
    changes = False
    mandatory_keys = ['name']
    for key in mandatory_keys:
        if key in data:
            if data[key] != getattr(role, key):
                setattr(role, key, data[key])
                changes = True

    if changes:
        db.session.add(role)
        db.session.commit()

    return ''


@api.route('/v1.0/users/<user_id>/roles/<role_id>', methods=['DELETE'])
@token_auth.login_required
def delete_role(user_id, role_id):
    """
    Delete an existing Role.

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
      - name: role_id
        in: path
        description: ID of the Role
        required: true
        type: integer
    responses:
      200:
        description: When successfull
      403:
        description: When forbidden by role
      404:
        description: When wrong user or wrong role
    """
    permission = RoleWritePermission()
    if not permission.can():
        raise RoleError(permission)

    role = Role.query.get_or_404(role_id)
    logger.warning(role.to_dict())
    if int(role.user_id) != int(user_id):
        abort(404)

    db.session.delete(role)
    db.session.commit()

    return ''
