"""All the tests of our project."""
import logging

from mock import patch
import pytest

from utils import TestAPI

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('app_class')
class TestRemoteProxy(TestAPI):
    """Test for celery."""

    def token_ping_side_effect(self, *args, **kwargs):
        """Global mock response for token.ping."""
        if self.return_ok:
            return True
        else:
            return False

    def salt_job_side_effect(self, *args, **kwargs):
        """Global mock response job.run."""
        if self.return_ok:
            function = self.salt_job_side_effect_ok
        else:
            function = self.salt_job_side_effect_ko
        return function(*args, **kwargs)

    def salt_job_side_effect_ok(self, *args, **kwargs):
        """Respond in a normal way to salt job."""
        minion = args[0]  # noqa
        function = args[1]  # noqa
        data = args[2]  # noqa

        if function == 'remote_control.create_ssh_connection':
            return {'pid': 1234}

        return {}

    def salt_job_side_effect_ko(self, *args, **kwargs):
        """Respond in a error way for salt job."""
        minion = args[0]  # noqa
        function = args[1]  # noqa
        data = args[2]  # noqa

        return {}

    @patch('projety.wsproxy.tokens.Token.ping')
    @patch('projety.salt.Job.run')
    def test_remote_token(self, mock_salt_job, mock_token_ping):
        """Test that the wsproxy send back data the way we want."""
        token = self.valid_token
        minion = self.valid_minion

        # Mock return
        mock_salt_job.side_effect = self.salt_job_side_effect
        mock_token_ping.side_effect = self.token_ping_side_effect

        # We start with ok values
        self.return_ok = True

        # Now get list
        r, s, h = self.get(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 204

        # Normal token create
        r, s, h = self.post(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 200
        assert 'token' in r
        r_token = r['token']

        # If we ask twice, we should have the same token
        r, s, h = self.post(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 200
        assert 'token' in r
        assert r['token'] == r_token

        # Now get list
        r, s, h = self.get(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 200
        for i in ['expiration', 'id', 'minion', 'last_seen']:
            assert i in r
        assert r['id'] == r_token

        # Delete token
        r, s, h = self.delete(
            '/api/v1.0/minions/{0}/remote/{1}'.format(minion, r_token),
            token_auth=token)
        logger.warning(r)
        assert s == 200

        # Test we have empty response
        r, s, h = self.get(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 204

        # Delete token that do not exist
        r, s, h = self.delete(
            '/api/v1.0/minions/{0}/remote/{1}'.format(minion, r_token),
            token_auth=token)
        assert s == 400

        # Now we want error value
        self.return_ok = False
        r, s, h = self.post(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 500
