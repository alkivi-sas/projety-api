"""All the tests of our project."""
import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestMinions(TestAPI):
    """Test for minions."""

    def test_minions(self):
        """Test the structure of return of the salt minions."""
        r, s, h = self.get('/api/v1.0/minions', token_auth=self.valid_token)
        assert s == 200
        assert isinstance(r, list)

    def test_get_task(self):
        """Test the structure of return of the salt minions."""
        token = self.valid_token
        minion = self.valid_minion

        r, s, h = self.get('/api/v1.0/minions/{0}/tasks'.format(minion),
                           token_auth=token)
        assert s == 200
        assert isinstance(r, list)

    def test_get_task_description(self):
        """Test the structure of return of the salt minions."""
        token = self.valid_token
        minion = self.valid_minion

        r, s, h = self.get('/api/v1.0/minions/{0}/tasks/{1}'.format(minion,
                           'test.ping'), token_auth=token)
        assert s == 200
        assert 'documentation' in r
