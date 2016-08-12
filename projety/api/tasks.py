"""Handles /keys endpoints."""
import logging

from flask import jsonify, abort
from celery import states

from ..salt import get_functions
from ..auth import token_auth
from ..utils import url_for
from . import api
from .async import run_flask_request


logger = logging.getLogger(__name__)


@api.route('/v1.0/tasks', methods=['GET'])
@token_auth.login_required
def get_salt_functions():
    """Return the list of all tasks we can do."""
    return jsonify(get_functions())


@api.route('/v1.0/tasks/status/<id>', methods=['GET'])
@token_auth.login_required
def get_status(id):
    """
    Return the status of a request.

    Return status about an asynchronous task. If this request returns a 202
    status code, it means that task hasn't finished yet. Else, the response
    from the task is returned.
    """
    task = run_flask_request.AsyncResult(id)
    if task.state == states.PENDING:
        abort(404)
    if task.state == states.RECEIVED or task.state == states.STARTED:
        return '', 202, {'Location': url_for('api.get_status', id=id)}
    return task.info
