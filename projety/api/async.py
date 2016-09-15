"""Handles /keys endpoints."""
import logging
import time
from functools import wraps
try:
    from io import BytesIO
except ImportError:  # pragma:  no cover
    from cStringIO import StringIO as BytesIO

from flask import g, request
from werkzeug.exceptions import InternalServerError
from celery import states

from .. import celery, socketio
from ..utils import url_for
from ..salt import (runner, client)

text_types = (str, bytes)
try:
    text_types += (unicode,)
except NameError:
    # no unicode on Python 3
    pass

logger = logging.getLogger(__name__)


@celery.task
def salt_socketio(jid, minion, sid):
    """Wait for a salt job and emit result."""
    from ..wsgi_aux import app
    with app.app_context():

        try:
            # Wait for salt-completion
            logger.warning('testing jid {0} on minion {1}'.format(jid, minion))
            status = client.cmd(minion, 'saltutil.find_job', [jid])

            time_iteration = 1
            while 'jid' in status:
                time.sleep(time_iteration)
                logger.warning('testing jid {0} on minion {1}'.format(
                    jid, minion))
                status = client.cmd(minion, 'saltutil.find_job', [jid])

            # When finish call salt-run
            result = runner.cmd('jobs.lookup_jid', [jid])

            if minion not in result:
                raise Exception('Wrong salt return')

            # Push data back
            socketio.emit('job_result',
                          {'jid': jid, 'status': 'success', 'result': result},
                          room=sid)
        except Exception as e:
            socketio.emit('job_result',
                          {'jid': jid, 'status': 'error', 'result': e.args[0]},
                          room=sid)


def salt_async(minion, task):
    """Apply async in the same way as async but no decorator."""
    # If we are on the Flask side, we need to launch the Celery task,
    # passing the request environment, which will be used to reconstruct
    # the request object. The request body has to be handled as a special
    # case, since WSGI requires it to be provided as a file-like object.
    environ = {k: v for k, v in request.environ.items()
               if isinstance(v, text_types)}
    if 'wsgi.input' in request.environ:
        environ['_wsgi.input'] = request.get_data()

    t = run_flask_request.apply_async(args=(environ,))

    # Return a 202 response, with a link that the client can use to
    # obtain task status that is based on the Celery task id.
    if t.state == states.PENDING or t.state == states.RECEIVED or \
            t.state == states.STARTED:
                return '', 202, {
                       'Location': url_for('api.get_status', id=t.id),
                       'Access-Control-Expose-Headers': 'Location'}

    # If the task already finished, return its return value as response.
    # This would be the case when CELERY_ALWAYS_EAGER is set to True.
    return t.info


@celery.task
def run_flask_request(environ):
    """Run our flask request using celery workers."""
    from ..wsgi_aux import app

    if '_wsgi.input' in environ:
        logger.warning(environ['_wsgi.input'])
        environ['wsgi.input'] = BytesIO(environ['_wsgi.input'])

    # Create a request context similar to that of the original request
    # so that the task can have access to flask.g, flask.request, etc.
    with app.request_context(environ):
        # Record the fact that we are running in the Celery worker now
        g.in_celery = True

        # Run the route function and record the response
        try:
            logger.warning('Going to run for environ')
            logger.warning(environ)
            rv = app.full_dispatch_request()
        except:
            # If we are in debug mode we want to see the exception
            # Else, return a 500 error
            if app.debug:
                raise
            rv = app.make_response(InternalServerError())
        return (rv.get_data(), rv.status_code, rv.headers)


def async(f):
    """
    Custom Decorator for async request.

    Decorator that transforms a sync route to asynchronous by running it
    in a background thread.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # If we are already running the request on the celery side, then we
        # just call the wrapped function to allow the request to execute.
        if getattr(g, 'in_celery', False):
            return f(*args, **kwargs)

        # If we are on the Flask side, we need to launch the Celery task,
        # passing the request environment, which will be used to reconstruct
        # the request object. The request body has to be handled as a special
        # case, since WSGI requires it to be provided as a file-like object.
        environ = {k: v for k, v in request.environ.items()
                   if isinstance(v, text_types)}
        if 'wsgi.input' in request.environ:
            environ['_wsgi.input'] = request.get_data()
        t = run_flask_request.apply_async(args=(environ,))

        # Return a 202 response, with a link that the client can use to
        # obtain task status that is based on the Celery task id.
        if t.state == states.PENDING or t.state == states.RECEIVED or \
                t.state == states.STARTED:
                    return '', 202, {
                           'Location': url_for('api.get_status', id=t.id),
                           'Access-Control-Expose-Headers': 'Location'}

        # If the task already finished, return its return value as response.
        # This would be the case when CELERY_ALWAYS_EAGER is set to True.
        return t.info
    return wrapped
