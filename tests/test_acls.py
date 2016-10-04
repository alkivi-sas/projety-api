"""All the tests of our project."""
import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestAcls(TestAPI):
    """Test for users."""

    def test_users_acl(self):
        """Test users ACL."""
        token = self.valid_token

        # get acls list for the first user
        url = '/api/v1.0/users/{0}/acls'.format(1)
        r, s, h = self.get(url, token_auth=token)
        assert s == 200
        assert isinstance(r, list)
        acl = r[0]['id']

        # get acl
        url = '/api/v1.0/users/{0}/acls/{1}'.format(1, acl)
        r, s, h = self.get(url, token_auth=token)
        assert s == 200
        assert isinstance(r, dict)
        for i in ['minions', 'id', 'functions']:
            assert i in r

        # get acl that dont exist for the user
        url = '/api/v1.0/users/{0}/acls/{1}'.format(1, 2)
        r, s, h = self.get(url, token_auth=token)
        logger.warning(r)
        assert s == 404
