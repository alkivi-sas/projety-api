"""All the tests of our project."""
import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestAsync(TestAPI):
    """Test for users."""

    def test_async_cors(self):
        """Test basic ping access."""
        token = self.valid_token
        minion = self.valid_minion

        # we test both sync and async
        r, s, h = self.post('/api/v1.0/tasks/ping/{0}'.format(minion),
                            token_auth=token)
        # During test we want 0 header
        assert len(h.getlist('Access-Control-Allow-Origin')) == 0
        assert len(h.getlist('Access-Control-Allow-Headers')) == 0
        assert len(h.getlist('Access-Control-Expose-Headers')) == 0
        assert len(h.getlist('Access-Control-Allow-Methods')) == 0
        assert len(h.getlist('Access-Control-Max-Age')) == 0
        assert len(h.getlist('Access-Control-Allow-Credentials')) == 0
        logger.warning(r)
        logger.warning(s)
        logger.warning(h)
        assert s == 200

        # check that we have the minion in keys
        assert minion in r
