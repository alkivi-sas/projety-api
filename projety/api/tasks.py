"""Handles /keys endpoints."""
import logging

from flask import jsonify
from celery import states

from ..exceptions import ValidationError
from ..salt import get_functions, Job
from ..auth import token_auth
from ..utils import url_for
from . import api
from .async import run_flask_request


logger = logging.getLogger(__name__)


@api.route('/v1.0/tasks', methods=['GET'])
@token_auth.login_required
def get_salt_functions():
    """
    Return the list of all tasks we can do.

    Return all the tasks we can do.
    ---
    tags:
      - tasks
    security:
      - token: []
    responses:
      200:
        description: Returns a lists of functions
        schema:
          type: array
          items:
            type: string
            description: function
    """
    return jsonify(get_functions())


@api.route('/v1.0/tasks/<string:task>', methods=['GET'])
@token_auth.login_required
def get_doc_function(task):
    """
    Return the documentation of a task.

    Return the documentation as present in salt.
    ---
    tags:
      - tasks
    security:
      - token: []
    parameters:
      - name: task
        in: path
        description: task to get doc for
        required: true
        type: string
    responses:
      200:
        description: Returns a lists of functions
    """
    if task not in get_functions():
        raise ValidationError('Task {0} is not valid'.format(task))

    job = Job()
    result = job.run('*', 'sys.doc', [task])
    return jsonify(result)


@api.route('/v1.0/tasks/status/<string:id>', methods=['GET'])
@token_auth.login_required
def get_status(id):
    """
    Return the status of a request.

    Return status about an asynchronous task. If this request returns a 202
    status code, it means that task hasn't finished yet. Else, the response
    from the task is returned.
    ---
    tags:
      - tasks
    security:
      - token: []
    parameters:
      - name: id
        in: path
        description: id of the task
        required: true
        type: string
    responses:
      202:
        description: The tasks in the finished yet
        headers:
          Location:
            description: The location to get final result
            type: string
      200:
        description: Real result of the task
    """
    task = run_flask_request.AsyncResult(id)
    if task.state in [states.PENDING, states.RECEIVED, states.STARTED]:
        return '', 202, {'Location': url_for('api.get_status', id=id),
                         'Access-Control-Expose-Headers': 'Location'}
    return task.info
