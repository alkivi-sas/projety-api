"""Generate and store token for remote control."""
from __future__ import absolute_import

import socket

import uuid
import time
import signal

import logging

from ..exceptions import SaltError, ValidationError
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
        self.uuid = uuid.uuid4().hex
        self.pid = None

        job = Job()
        result = job.run(minion,
                         'remote_control.create_ssh_connection',
                         [self.port])

        if not result:
            raise SaltError('Unable to create secure connection to' +
                            '{0}'.format(minion))
        if 'pid' not in result:
            raise SaltError('Unable to get pid of tunnel on ' +
                            '{0}'.format(minion))
        self.pid = result['pid']

    def exit_gracefully(self, signum, frame):
        """Close connection."""
        self._close_connection()

    def __repr__(self):
        """Custom representation."""
        return 'Token for {0}, last-seen {1}, expiration {2}'.format(
            self.minion,
            self.last_seen,
            self.expiration)

    def serialize(self):
        """Return a nice dict."""
        return {'id': self.uuid,
                'minion': self.minion,
                'last_seen': self.last_seen,
                'expiration': self.expiration}

    def __del__(self):
        """On token deletion, close pid."""
        logger.info('deleting token {0}'.format(self))
        self._close_connection()

    def _close_connection(self):
        """Terminate a connection."""
        if self.pid:
            job = Job(async=True)
            job.run(self.minion,
                    'remote_control.close_ssh_connection',
                    [self.pid])

    def refresh(self):
        """Refresh last_seen property."""
        self.last_seen = int(time.time())

    def is_expired(self):
        """Return whether a token is expired or not."""
        now = int(time.time())
        return now - self.last_seen > self.expiration

    def ping(self):
        """Check if the socket is still open."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', self.port))
            return True
        except:
            return False


class TokenManager(object):
    """Manage all the token created during the app lifetime."""

    def __init__(self):
        """Init our token manager."""
        self.tokens = {}
        self.uuids = {}

    def _create_token(self, minion, expiration):
        """Really create a token."""
        token = Token(minion, expiration=expiration)
        self.tokens[minion] = token
        self.uuids[token.uuid] = token
        return token

    def create_token(self, minion, expiration=3600):
        """Create a new token for a minion."""
        if minion in self.tokens:
            token = self.tokens[minion]
            if token.ping():
                token.refresh()
                return token
            else:
                # Clean token
                self._delete_token(token.minion, token.uuid)
                return self._create_token(minion, expiration)
        else:
            return self._create_token(minion, expiration)

    def get_token(self, token):
        """Try to fetch a token."""
        if token not in self.uuids:
            return False
        return self.uuids[token]

    def get_minion_token(self, minion):
        """Try to fetch a token for a minion."""
        if minion not in self.tokens:
            return False
        return self.tokens[minion]

    def delete_token(self, token):
        """Try to delete a token."""
        token = self.get_token(token)
        if not token:
            raise ValidationError('Token {0} not found'.format(token))
        else:
            uuid = token.uuid
            minion = token.minion
            return self._delete_token(minion, uuid)

    def _delete_token(self, minion, uid):
        """Clean all references to the token."""
        del self.tokens[minion]
        del self.uuids[uid]

    def clean_old_tokens(self):
        """
        Will check which token needs to be deleted.

        It will send a salt job to kill the minion pid
        """
        to_delete = []
        for minion, token in self.tokens.iteritems():
            if token.is_expired():
                # Not deleting directly, because of iteritems
                to_delete.append((minion, token.uuid))

        for minion, uid in to_delete:
            self._delete_token(minion, uuid)
