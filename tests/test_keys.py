"""All the tests of our project."""
import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestKeys(TestAPI):
    """Test for keys."""

    def test_keys(self):
        """Test the structure of return of the salt keys."""
        r, s, h = self.get('/api/v1.0/keys', token_auth=self.valid_token)
        assert s == 200
        for subkeys in ['local', 'minions', 'minions_denied', 'minions_pre',
                        'minions_rejected']:
            assert subkeys in r
