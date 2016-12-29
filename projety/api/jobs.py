"""Handles background jobs."""
import logging
import threading
import time

from flask import current_app

from ..salt import Job, get_minions
from . import api

logger = logging.getLogger(__name__)


@api.before_app_first_request
def cleaning():
    """Start a background thread to clean old tokens."""
    def clean_old_tokens(app):
        with app.app_context():
            logger.info('thread clean_old_tokens started')
            while True:
                websockify = app.extensions['websockify']
                token_manager = websockify.server.token_manager
                token_manager.clean_old_tokens()
                time.sleep(app.config['CLEANING_SLEEP'])

    if 'websockify' in current_app.extensions:
        if not current_app.config['TESTING']:
            thread = threading.Thread(
                target=clean_old_tokens,
                args=(current_app._get_current_object(),))
            thread.start()


@api.before_app_first_request
def auto_ping():
    """Start a background thread to ping all minions."""
    def ping_all_minions(app):
        with app.app_context():
            logger.info('thread ping_all_minions started')
            while True:
                socketio = app.extensions['socketio']
                job = Job(only_one=False, bypass_check=True)
                result = job.run('*', 'test.ping', timeout=10)

                # Build return
                minions = get_minions()

                for minion in minions:
                    if minion not in result:
                        result[minion] = False

                # Push data back using socketio
                socketio.emit('auto_ping', result)

                # Sleep 30 seconds between calls
                time.sleep(app.config['AUTO_PING_SLEEP'])

    if 'socketio' in current_app.extensions:
        if not current_app.config['TESTING']:
            thread = threading.Thread(
                target=ping_all_minions,
                args=(current_app._get_current_object(),))
            thread.start()
