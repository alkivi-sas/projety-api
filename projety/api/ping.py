"""Handles /keys endpoints."""
import logging

from flask import abort, request, jsonify

from ..exceptions import ValidationError
from ..salt import wheel, Job
from ..auth import token_auth
from . import api
from .async import async

logger = logging.getLogger(__name__)


def _ping_one(minion):
    """Return a simple test.ping."""
    all_keys = wheel.cmd('key.list_all')
    keys = all_keys['minions']
    if minion not in keys:
        abort(404)

    logger.debug('going to ping {0}'.format(minion))
    job = Job()
    result = job.run(minion, 'test.ping')
    return jsonify(result)


def _ping():
    """Return the simple test.ping but can be on a list."""
    data = request.json
    if not data:
        raise ValidationError('no json data in request')

    if 'target' not in data:
        raise ValidationError('no target in parameters')
    targets = data['target']

    to_test = None
    if isinstance(targets, list):
        to_test = targets
    elif isinstance(targets, (str, unicode)):
        to_test = [targets]
    else:
        raise ValidationError('target parameter is not an array not a scalar')

    all_keys = wheel.cmd('key.list_all')
    keys = all_keys['minions']

    minions = []
    for m in to_test:
        if m in keys:
            minions.append(m)

    if not minions:
        abort(404)

    real_target = ','.join(minions)
    logger.debug('Going to ping {0} as a list'.format(real_target))
    job = Job()
    result = job.run(real_target, 'test.ping', expr_form='list')
    return jsonify(result)


@api.route('/v1.0/ping/<minion>', methods=['POST'])
@token_auth.login_required
def ping_one(minion):
    """
    Perform synchronous test.ping on a minion.

    Before performing the task, ensure that the minion is present
    in keys. Return 404 if not
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
            - minion
          properties:
            minion:
              type: boolean
      404:
        description: The minion is not in the valid keys
    """
    return _ping_one(minion)


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
      404:
        description: All the minions are not in the valid keys
    """
    return _ping()


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
          $ref: '#/definitions/api_ping_one_post_ping_one'
      404:
        description: The minion is not in the valid keys
    """
    return _ping_one(minion)


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
      404:
        description: All the minions are not in the valid keys
    """
    return _ping()
