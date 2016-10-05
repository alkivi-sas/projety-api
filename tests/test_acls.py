"""All the tests of our project."""
import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestAcls(TestAPI):
    """Test for users."""

    def test_users_salt_call(self):
        """Test Salt ACL."""
        minion = self.valid_minion

        admin_token = self.get_valid_token('admin')

        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.ping')
        data = {'async': 'sync'}
        r, s, h = self.post(url, data=data, token_auth=admin_token)
        logger.warning(r)
        assert s == 200
        assert minion in r

        restricted_token = self.get_valid_token('restricted')

        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.ping')
        data = {'async': 'sync'}
        r, s, h = self.post(url, data=data, token_auth=restricted_token)
        logger.warning(r)
        assert s == 403

        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion,
                                                       'network.ip_addrs')
        data = {'async': 'sync'}
        r, s, h = self.post(url, data=data, token_auth=restricted_token)
        logger.warning(r)
        assert s == 200

    def test_users_acl(self):
        """Test users ACL."""
        admin_token = self.get_valid_token('admin')
        admin = self.get_user('admin')
        mandatory_keys = ['minions', 'id', 'functions', 'user_id']

        # get acls list for the admin user
        url = '/api/v1.0/users/{0}/acls'.format(admin.id)
        r, s, h = self.get(url, token_auth=admin_token)
        assert s == 200
        assert isinstance(r, list)
        admin_acl = r[0]['id']

        # get acl for admin
        url = '/api/v1.0/users/{0}/acls/{1}'.format(admin.id, admin_acl)
        r, s, h = self.get(url, token_auth=admin_token)
        assert s == 200
        assert isinstance(r, dict)
        for i in ['minions', 'id', 'functions', 'user_id']:
            assert i in r

        restricted_token = self.get_valid_token('restricted')
        restricted = self.get_user('restricted')

        # get acls list for the restricted user
        url = '/api/v1.0/users/{0}/acls'.format(restricted.id)
        r, s, h = self.get(url, token_auth=restricted_token)
        assert s == 200
        assert isinstance(r, list)
        restricted_acl = r[0]['id']

        # get acl for restricted
        url = '/api/v1.0/users/{0}/acls/{1}'.format(restricted.id,
                                                    restricted_acl)
        r, s, h = self.get(url, token_auth=restricted_token)
        assert s == 200
        assert isinstance(r, dict)
        for i in mandatory_keys:
            assert i in r

        # Now check that admin can see restricted acl
        url = '/api/v1.0/users/{0}/acls/{1}'.format(restricted.id,
                                                    restricted_acl)
        r, s, h = self.get(url, token_auth=admin_token)
        assert s == 200
        assert isinstance(r, dict)
        for i in mandatory_keys:
            assert i in r

        # But not the other way around
        url = '/api/v1.0/users/{0}/acls/{1}'.format(admin.id,
                                                    admin_acl)
        r, s, h = self.get(url, token_auth=restricted_token)
        assert s == 403

        # Now add a new acl to restricted
        data = {'minions': self.valid_minion, 'functions': 'test.ping'}
        url = '/api/v1.0/users/{0}/acls'.format(restricted.id)
        r, s, h = self.post(url, data=data, token_auth=admin_token)
        logger.warning(r)
        assert s == 200
        assert 'id' in r
        new_acl_id = r['id']

        # Post twice with the same : error
        r, s, h = self.post(url, data=data, token_auth=admin_token)
        logger.warning(r)
        assert s == 400

        # Post using restricted : error
        r, s, h = self.post(url, data=data, token_auth=restricted_token)
        logger.warning(r)
        assert s == 403

        # Put acl as admin
        data = {'functions': 'test.*'}
        url = '/api/v1.0/users/{0}/acls/{1}'.format(restricted.id, new_acl_id)
        r, s, h = self.put(url, data=data, token_auth=admin_token)
        logger.warning(r)
        assert s == 200

        # Put acl as restricted
        r, s, h = self.put(url, data=data, token_auth=restricted_token)
        logger.warning(r)
        assert s == 403

        # Get modified acl
        r, s, h = self.get(url, token_auth=restricted_token)
        logger.warning(r)
        assert s == 200
        assert r['minions'] == self.valid_minion
        assert r['functions'] == 'test.*'

        # Delete acl as restricted
        r, s, h = self.delete(url, token_auth=restricted_token)
        logger.warning(r)
        assert s == 403

        # Delete acl as admin
        r, s, h = self.delete(url, token_auth=admin_token)
        logger.warning(r)
        assert s == 200

        # Get old acl
        r, s, h = self.get(url, token_auth=admin_token)
        logger.warning(r)
        assert s == 404
