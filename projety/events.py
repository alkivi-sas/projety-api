"""Handle socket.io events."""

import logging

from flask import g, request

from . import socketio, celery
from .models import User
from .auth import verify_token, verify_password
from .salt import ping_one
from .exceptions import SaltError, ValidationError

logger = logging.getLogger(__name__)


def push_result(data, sid):
    """Push the job to all connected Socket.IO clients."""
    socketio.emit('job_result', data, room=sid)


@celery.task
def ping_minion(user_id, data, sid):
    """Run the ping task using socket.io and celery dispatch."""
    from .wsgi_aux import app
    with app.app_context():
        user = User.query.get(user_id)
        if user is None:
            return

        # Installing current_user
        g.current_user = user

        # Run the salt Job
        minion = data['minion']
        try:
            result = ping_one(minion)
        except SaltError as e:
            result = e.to_dict()
        except ValidationError as e:
            result = e.to_dict()
        push_result(result, sid)


@socketio.on('login')
def on_login(nickname, password, expiration=600):
    """Callback from socket.io client on webapp."""
    if verify_password(nickname, password):
        token = g.current_user.generate_auth_token(expiration)
        socketio.emit('login', {'token': token}, room=request.sid)
    else:
        socketio.emit('login_error', {'error': 'wrong login'},
                      room=request.sid)


@socketio.on('sid')
def on_get_sid(token):
    """Callback to get sid."""
    verify_token(token)
    if g.current_user:
        socketio.emit('sid', {'sid': request.sid}, room=request.sid)


@socketio.on('ping_minion')
def on_ping_minion(data, token):
    """Callback from socket.io client on webapp."""
    verify_token(token)
    if g.current_user:
        ping_minion.apply_async(args=(g.current_user.id, data,
                                      request.sid))
