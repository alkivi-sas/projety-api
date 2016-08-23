"""Handles /keys endpoints."""
import logging

from flask import jsonify

from ..exceptions import SaltError
from ..salt import wheel, Job
from ..auth import token_auth
from . import api

logger = logging.getLogger(__name__)


@api.route('/v1.0/minions', methods=['GET'])
@token_auth.login_required
def get_keys():
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
    """
    keys = wheel.cmd('key.list_all')
    if 'minions' not in keys:
        raise SaltError('No minions in key.list_all')
    return jsonify(keys['minions'])


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
    """
    job = Job()
    result = job.run(minion, 'sys.list_functions')
    if minion not in result:
        raise SaltError('minion {0} not in salt return'.format(minion))
    return jsonify(result[minion])


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
    """
    job = Job()
    result = job.run(minion, 'sys.doc', [task])
    logger.error(result)
    if minion not in result:
        raise SaltError('minion {0} not in salt return'.format(minion))
    if task not in result[minion]:
        raise SaltError('task {0} not in salt return'.format(task))
    return jsonify({'documentation': result[minion][task]})
