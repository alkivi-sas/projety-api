"""Generate and store token for remote control."""

import uuid
import time
import signal

import logging

from ..exceptions import SaltError
from ..utils import get_open_port
from ..salt import Job

logger = logging.getLogger(__name__)


class Token(object):
    """Manage a token for a minion."""

    def __init__(self, minion, expiration=3600):
        """Init."""
        # We want connection to close correctly
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        self.minion = minion
        self.last_seen = int(time.time())
        self.port = get_open_port()
        self.expiration = expiration

        job = Job()
        result = job.run(minion,
                         'remote_control.create_ssh_connection',
                         [self.port])

        if not result:
            raise SaltError('Unable to create secure connection to' +
                            '{0}'.format(minion))
        if 'pid' not in result:
            raise SaltError('Unable to get pid of tunnel connection' +
                            '{0}'.format(minion))
        self.pid = result['pid']
        self.uuid = uuid.uuid4().hex

    def exit_gracefully(self, signum, frame):
        """Close connection."""
        self._close_connection()

    def __repr__(self):
        """Custom representation."""
        return 'Token for {0}, last-seen {1}, expiration {2}'.format(
            self.minion,
            self.last_seen,
            self.expiration)

    def __del__(self):
        """On token deletion, close pid."""
        logger.info('deleting token {0}'.format(self))
        self._close_connection()

    def _close_connection(self):
        """Terminate a connection."""
        job = Job(async=True)
        job.run(self.minion, 'remote_control.close_ssh_connection', [self.pid])

    def refresh(self):
        """Refresh last_seen property."""
        self.last_seen = int(time.time())

    def is_expired(self):
        """Return whether a token is expired or not."""
        now = int(time.time())
        return now - self.last_seen > self.expiration


class TokenManager(object):
    """Manage all the token created during the app lifetime."""

    def __init__(self):
        """Init our token manager."""
        self.tokens = {}
        self.uuids = {}

    def create_token(self, minion, expiration=3600):
        """Create a new token for a minion."""
        if minion in self.tokens:
            token = self.tokens[minion]
            token.refresh()
            return token
        else:
            token = Token(minion, expiration=expiration)
            self.tokens[minion] = token
            self.uuids[token.uuid] = token
            return token

    def get_token(self, token):
        """Try to fetch a token."""
        if token not in self.uuids:
            return False
        return self.uuids[token]

    def clean_old_tokens(self):
        """
        Will check which token needs to be deleted.

        It will send a salt job to kill the minion pid
        """
        to_delete = []
        for minion, token in self.tokens.iteritems():
            if token.is_expired():
                to_delete.append((minion, token.uuid))

        for minion, uid in to_delete:
            del self.tokens[minion]
            del self.uuids[uid]
