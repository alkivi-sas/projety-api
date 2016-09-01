"""Handles /keys endpoints."""
import logging

from flask import jsonify

from ..exceptions import SaltError, ValidationError
from ..salt import (get_minions as _get_minions,
                    get_minion_functions as _get_minion_functions,
                    Job)
from ..auth import token_auth
from ..utils import get_open_port
from . import api

logger = logging.getLogger(__name__)


@api.route('/v1.0/minions', methods=['GET'])
@token_auth.login_required
def get_minions():
    """
    Return the list of salt keys.

    ---
    tags:
      - minions
    security:
      - token: []
    responses:
      200:
        description: Returns the lists of keys
        schema:
          id: keys
          type: array
          items:
            type: string
      500:
        description: Error in salt return
    """
    return jsonify(_get_minions(use_cache=False))


@api.route('/v1.0/minions/<string:minion>/tasks', methods=['GET'])
@token_auth.login_required
def get_minion_functions(minion):
    """
    Return the list of all tasks we can do.

    Return all the tasks we can do.
    ---
    tags:
      - minions
    security:
      - token: []
    parameters:
      - name: minion
        in: path
        description: target
        required: true
        type: string
    responses:
      200:
        description: Returns a lists of functions
        schema:
          type: array
          items:
            type: string
            description: function
      400:
        description: Minion is not found
      500:
        description: Error in salt return
    """
    return jsonify(_get_minion_functions(minion))


@api.route('/v1.0/minions/<string:minion>/tasks/<string:task>',
           methods=['GET'])
@token_auth.login_required
def get_minion_function(minion, task):
    """
    Return the documentation of a task.

    Return the salt documentation of the task.
    ---
    tags:
      - minions
    security:
      - token: []
    parameters:
      - name: minion
        in: path
        description: target
        required: true
        type: string
      - name: task
        in: path
        description: task wanted for documentation
        required: true
        type: string
    responses:
      200:
        description: Returns a lists of functions
        schema:
          id: doc
          required:
            - documentation
          properties:
            documentation:
              type: string
      400:
        description: Minion or task is not found
      500:
        description: Error in salt return
    """
    if task not in _get_minion_functions(minion):
        raise ValidationError('task {0} not valid'.format(task))

    job = Job()
    result = job.run(minion, 'sys.doc', [task])
    if task not in result:
        raise SaltError('task {0} not in salt return'.format(task))
    return jsonify({'documentation': result[task]})


@api.route('/v1.0/minions/<string:minion>/remote',
           methods=['GET'])
@token_auth.login_required
def get_remote(minion):
    """
    Return the documentation of a task.

    Return the salt documentation of the task.
    ---
    tags:
      - minions
    security:
      - token: []
    parameters:
      - name: minion
        in: path
        description: target
        required: true
        type: string
    responses:
      200:
        description: TODO
    """
    port = get_open_port()

    job = Job()
    result = job.run(minion, 'projety.create_ssh_connection', [port])

    if not result:
        raise SaltError('Unable to create secure connection to' +
                        '{0}'.format(minion))

    return jsonify({'port': port, 'pid': result})
