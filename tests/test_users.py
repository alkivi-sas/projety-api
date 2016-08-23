"""All the tests of our project."""
import logging

from utils import TestAPI
from time import sleep

logger = logging.getLogger(__name__)


class TestUsers(TestAPI):
    """Test for users."""

    def test_users(self):
        """Test user access with or without token."""
        # get users without auth
        r, s, h = self.get('/api/v1.0/users')
        assert s == 401

        # get users with bad auth
        r, s, h = self.get('/api/v1.0/users', token_auth='bad-token')
        assert s == 401

        # request a token with wrong password
        r, s, h = self.post('/api/v1.0/tokens', basic_auth='alkivi:toto')
        assert s == 401

        # request a token
        r, s, h = self.post('/api/v1.0/tokens', basic_auth='alkivi:alkivi123')
        assert s == 200
        token = r['token']

        # get users with good token
        r, s, h = self.get('/api/v1.0/users', token_auth=token)
        assert s == 200

        # request a token with wrong expiration
        r, s, h = self.post('/api/v1.0/tokens?expiration=toto',
                            basic_auth='alkivi:alkivi123')
        assert s == 400

        # request short token
        r, s, h = self.post('/api/v1.0/tokens?expiration=1',
                            basic_auth='alkivi:alkivi123')
        assert s == 200
        token = r['token']

        # sleep to expire token
        sleep(2)

        # use invalid token now
        r, s, h = self.get('/api/v1.0/users', token_auth=token)
        assert s == 401
