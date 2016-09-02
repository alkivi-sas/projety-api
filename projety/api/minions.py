"""Handles /keys endpoints."""
import logging
import threading
import time

from flask import jsonify, current_app


from ..exceptions import SaltError, ValidationError
from ..salt import (get_minions as _get_minions,
                    get_minion_functions as _get_minion_functions,
                    Job)
from ..auth import token_auth
from .. import wsproxy
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
    Return a valid token in order to connect to a minion.

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
        description: Returns a valid token
        schema:
          id: remote
          required:
            - token
          properties:
            token:
              type: string
    """
    token = wsproxy.create_token(minion, expiration=3600)
    return jsonify({'token': token.uuid})

@api.before_app_first_request
def before_first_request():
    """Start a background thread to clean old tokens."""
    def clean_old_tokens(app):
        with app.app_context():
            while True:
                websockify = app.extensions['websockify']
                token_manager = websockify.server.token_manager
                token_manager.clean_old_tokens()
                time.sleep(5)

    if 'websockify' in current_app.extensions:
        if not current_app.config['TESTING']:
            thread = threading.Thread(
                target=clean_old_tokens,
                args=(current_app._get_current_object(),))
            thread.start()
