"""All the tests of our project."""

import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestPing(TestAPI):
    """Test for users."""

    def test_ping_one(self):
        """Test basic ping access."""
        token = self.valid_token
        minion = self.valid_minion

        # ping one minion
        logger.warning('Going to ping {0}'.format(minion))
        r, s, h = self.post('/api/v1.0/ping/{0}'.format(minion),
                            token_auth=token)
        assert s == 200

        # check that we have the minion in keys
        assert minion in r

    def test_ping(self):
        """Test several pings."""
        token = self.valid_token
        minion = self.valid_minion

        r, s, h = self.post('/api/v1.0/ping', data={'target': [minion]},
                            token_auth=token)

        # check that we have the minion in keys
        assert minion in r
