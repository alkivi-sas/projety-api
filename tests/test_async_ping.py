"""All the tests of our project."""
import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestAsyncPing(TestAPI):
    """Test for users."""

    def test_async_ping_one(self):
        """Test basic ping access."""
        token = self.valid_token
        minion = self.valid_minion

        # ping one minion
        r, s, h = self.post('/api/v1.0/tasks/ping/{0}'.format(minion),
                            token_auth=token)
        assert s == 200

        # check that we have the minion in keys
        assert minion in r

    def test_async_ping(self):
        """Test several pings."""
        token = self.valid_token
        minion = self.valid_minion

        r, s, h = self.post('/api/v1.0/tasks/ping', data={'target': [minion]},
                            token_auth=token)
        assert s == 200

        # check that we have the minion in keys
        assert minion in r
