"""Handles /keys endpoints."""
import logging
import threading
import time

from flask import jsonify, current_app, request, g


from ..exceptions import SaltError, ValidationError
from ..salt import (get_minions as _get_minions,
                    get_minion_functions as _get_minion_functions,
                    Job, is_task_allowed)
from ..auth import token_auth
from .. import remote_proxy
from . import api
from async import salt_async, salt_socketio

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
def get_minion_tasks(minion):
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
def get_minion_task(minion, task):
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


@api.route('/v1.0/minions/<string:minion>/tasks/<string:task>',
           methods=['POST'])
@token_auth.login_required
def post_minion_task(minion, task):
    """
    Return a salt jobid.

    If socketio is defined (default to Yes), the result will be send back
    using socketio.
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
      - name: async_data
        in: body
        description: async mode
        required: false
        schema:
          id: async_mode
          properties:
            async:
              description: async mode
              type: string
              default: async
              enum:
                - async
                - sync
                - socket.io
            sid:
              description: sid for socket.io
              type: string
    responses:
      200:
        description: Return the result in sync mode
        schema:
          id: result
          required:
            - result
          properties:
            result:
              type: string
      201:
        description: Return a salt job id (jid) in socket.io mode
        schema:
          id: job
          required:
            - jid
          properties:
            jid:
              type: integer
      202:
        description: Return the location in async mode
        headers:
          Location:
            description: The location to get final result of the task
            type: string
      400:
        description: Minion or task is not found
      403:
        description: ACL deny access to this task
      500:
        description: Error in salt return
    """
    data = request.json

    if 'async' not in data:
        async = 'sync'
    else:
        async = data['async']

    if async not in ['async', 'sync', 'socket.io']:
        raise ValidationError('async mode {0} not valid'.format(async))

    if async == 'socket.io':
        if 'sid' not in data:
            raise ValidationError('must pass sid when using socket.io')
        else:
            sid = data['sid']

    if task not in _get_minion_functions(minion):
        raise ValidationError('task {0} not valid'.format(task))

    is_task_allowed(task)

    if async == 'socket.io':
        job = Job(async=True)
        jid = job.run(minion, task)
        salt_socketio.apply_async(args=(jid, minion, sid))
        return jsonify({'jid': jid})

    if async == 'async':
        # If run from celery, then run sync
        if getattr(g, 'in_celery', False):
            async = 'sync'
        else:
            return salt_async(minion, task)

    if async == 'sync':
        job = Job(async=False)
        result = job.run(minion, task)
        return jsonify({minion: result})


@api.route('/v1.0/minions/<string:minion>/remote',
           methods=['POST'])
@token_auth.login_required
def post_remote(minion):
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
    token = remote_proxy.create_token(minion, expiration=3600)
    return jsonify({'token': token.uuid})


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
        description: Return token if it exist
        schema:
          id: token
          required:
            - id
            - minion
            - expiration
            - last_seen
          properties:
            id:
              type: string
            minion:
              type: string
            expiration:
              type: string
            last_seen:
              type: string
      204:
        description: When no token exists.
        schema:
          ref: $TODO
    """
    t = remote_proxy.get_token(minion)
    if not t:
        return '', 204
    else:
        return jsonify(t.serialize())


@api.route('/v1.0/minions/<string:minion>/remote/<string:token>',
           methods=['DELETE'])
@token_auth.login_required
def del_remote_token(minion, token):
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
      - name: token
        in: path
        description: target
        required: true
        type: string
    responses:
      200:
        description: When a token is delete
      400:
        description: When a token is not found
    """
    remote_proxy.delete_token(token)
    return ''


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
