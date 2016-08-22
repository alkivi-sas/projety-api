"""Handle socket.io events."""

import logging

from flask import g

from . import socketio, celery
from .models import User
from .auth import verify_token
from .salt import Job

logger = logging.getLogger(__name__)


def push_result(data):
    """Push the job to all connected Socket.IO clients."""
    socketio.emit('job_result', data)


@celery.task
def ping_minion(user_id, data):
    """Run the ping task using socket.io and celery dispatch."""
    from .wsgi_aux import app
    with app.app_context():
        user = User.query.get(user_id)
        if user is None:
            return

        # Run the salt Job
        minion = data['minion']
        job = Job()
        result = job.run(minion, 'test.ping')
        push_result(result)


@socketio.on('ping_minion')
def on_ping_minion(data, token):
    """Callback from socket.io client on webapp."""
    verify_token(token)
    logger.warning('on_ping_user')
    if g.current_user:
        ping_minion.apply_async(args=(g.current_user.id, data))
