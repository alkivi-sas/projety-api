"""All the tests of our project."""

from utils import TestAPI


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

        # revoke token
        r, s, h = self.delete('/api/v1.0/tokens', token_auth=token)
        assert s == 204

        # use invalid token
        r, s, h = self.get('/api/v1.0/users', token_auth=token)
        assert s == 401
