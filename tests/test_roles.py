"""All the tests of our project."""
import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestRoles(TestAPI):
    """Test for users."""

    def test_users_role(self):
        """Test access of roles."""
        admin_token = self.get_valid_token('admin')
        admin = self.get_user('admin')
        mandatory_keys = ['id', 'name', 'user_id']

        # get roles list for the admin user
        url = '/api/v1.0/users/{0}/roles'.format(admin.id)
        r, s, h = self.get(url, token_auth=admin_token)
        assert s == 200
        assert isinstance(r, list)
        admin_role = r[0]['id']

        # get role for admin
        url = '/api/v1.0/users/{0}/roles/{1}'.format(admin.id, admin_role)
        r, s, h = self.get(url, token_auth=admin_token)
        assert s == 200
        assert isinstance(r, dict)
        for i in mandatory_keys:
            assert i in r

        restricted_token = self.get_valid_token('restricted')
        restricted = self.get_user('restricted')

        # get roles list for the restricted user
        url = '/api/v1.0/users/{0}/roles'.format(restricted.id)
        r, s, h = self.get(url, token_auth=restricted_token)
        assert s == 200
        assert isinstance(r, list)
        restricted_role = r[0]['id']

        # get role for restricted
        url = '/api/v1.0/users/{0}/roles/{1}'.format(restricted.id,
                                                     restricted_role)
        r, s, h = self.get(url, token_auth=restricted_token)
        assert s == 200
        assert isinstance(r, dict)
        for i in mandatory_keys:
            assert i in r

        # Now check that admin can see restricted role
        url = '/api/v1.0/users/{0}/roles/{1}'.format(restricted.id,
                                                     restricted_role)
        r, s, h = self.get(url, token_auth=admin_token)
        assert s == 200
        assert isinstance(r, dict)
        for i in mandatory_keys:
            assert i in r

        # But not the other way around
        url = '/api/v1.0/users/{0}/roles/{1}'.format(admin.id,
                                                     admin_role)
        r, s, h = self.get(url, token_auth=restricted_token)
        assert s == 403

        # Now add a new role to restricted
        data = {'name': 'toto'}
        url = '/api/v1.0/users/{0}/roles'.format(restricted.id)
        r, s, h = self.post(url, data=data, token_auth=admin_token)
        logger.warning(r)
        assert s == 200
        assert 'id' in r
        new_role_id = r['id']

        # Post twice with the same : error
        r, s, h = self.post(url, data=data, token_auth=admin_token)
        logger.warning(r)
        assert s == 400

        # Post using restricted : error
        r, s, h = self.post(url, data=data, token_auth=restricted_token)
        logger.warning(r)
        assert s == 403

        # Put role as admin
        data = {'name': 'tata'}
        url = '/api/v1.0/users/{0}/roles/{1}'.format(restricted.id,
                                                     new_role_id)
        r, s, h = self.put(url, data=data, token_auth=admin_token)
        logger.warning(r)
        assert s == 200

        # Put role as restricted
        r, s, h = self.put(url, data=data, token_auth=restricted_token)
        logger.warning(r)
        assert s == 403

        # Get modified role
        r, s, h = self.get(url, token_auth=restricted_token)
        logger.warning(r)
        assert s == 200
        assert r['name'] == 'tata'

        # Delete role as restricted
        r, s, h = self.delete(url, token_auth=restricted_token)
        logger.warning(r)
        assert s == 403

        # Delete role as admin
        r, s, h = self.delete(url, token_auth=admin_token)
        logger.warning(r)
        assert s == 200

        # Get old role
        r, s, h = self.get(url, token_auth=admin_token)
        logger.warning(r)
        assert s == 404
