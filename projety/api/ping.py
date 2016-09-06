"""Handles /keys endpoints."""
import logging

from flask import jsonify

from ..salt import (ping_one as _ping_one, ping as _ping)
from ..auth import token_auth
from . import api
from .async import async

logger = logging.getLogger(__name__)


@api.route('/v1.0/minions/<string:minion>/ping', methods=['POST'])
@api.route('/v1.0/ping/<string:minion>', methods=['POST'])
@token_auth.login_required
def ping_one(minion):
    """
    Perform synchronous test.ping on a minion.

    Before performing the task, ensure that the minion is present
    in keys. Return 400 if not.
    ---
    tags:
      - ping
    security:
      - token: []
    parameters:
      - name: minion
        in: path
        description: minion to ping
        required: true
        type: string
    responses:
      200:
        description: Returns the result
        schema:
          id: ping_one
          required:
            - minion1
          properties:
            minion1:
              type: boolean
      400:
        description: When minion is not found
    """
    return jsonify(_ping_one(minion))


@api.route('/v1.0/ping', methods=['POST'])
@token_auth.login_required
def ping():
    """
    Perform synchronous test.ping on a list of minions.

    Before performing the task, ensure that all the minions are present
    in keys. All minions that are not in the keys are removed.
    ---
    tags:
      - ping
    security:
      - token: []
    parameters:
      - name: target
        in: body
        description: minion to ping
        required: true
        schema:
          id: target_ping
          properties:
            target:
              description: target to ping
              type: array
              items:
                type: string
    responses:
      200:
        description: Returns the result
        schema:
          id: ping
          required:
            - minion1
            - minion2
          properties:
            minion1:
              type: boolean
            minion2:
              type: boolean
      400:
        description: When all minions are not found
    """
    return jsonify(_ping())


@api.route('/v1.0/tasks/ping/<minion>', methods=['POST'])
@async
@token_auth.login_required
def async_ping_one(minion):
    """
    Perform asynchronous test.ping.

    Before performing the task, ensure that all the minions are present
    in keys. All minions that are not in the keys are removed.
    ---
    tags:
      - tasks
    security:
      - token: []
    parameters:
      - name: minion
        in: path
        description: minion to ping
        required: true
        type: string
    responses:
      202:
        description: While the task is pending
        headers:
          Location:
            description: The location to get final result of the task
            type: string
      200:
        description: When the task is finished
        schema:
          $ref: '#/definitions/api_ping_post_ping'
      400:
        description: The minion is not in the valid keys
    """
    return jsonify(_ping_one(minion))


@api.route('/v1.0/tasks/ping', methods=['POST'])
@async
@token_auth.login_required
def async_ping():
    """
    Perform asynchronous test.ping on a list of minions.

    Before performing the task, ensure that all the minions are present
    in keys. All minions that are not in the keys are removed.
    ---
    tags:
      - tasks
    security:
      - token: []
    parameters:
      - name: target
        in: body
        description: minion to ping
        required: true
        schema:
          $ref: '#/definitions/api_ping_post_target_ping'
    responses:
      202:
        description: While the task is pending
        headers:
          Location:
            description: The location to get final result of the task
            type: string
      200:
        description: When the task is finished
        schema:
          $ref: '#/definitions/api_ping_post_ping'
      400:
        description: All the minions are not in the valid keys
    """
    return jsonify(_ping())
