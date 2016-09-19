"""All the tests of our project."""
import logging

from mock import patch
import pytest

from projety.salt import Job
from projety.api.async import async
from utils import TestAPI

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('app_class')
class TestRemoteProxy(TestAPI):
    """Test for celery."""

    def job_side_effect(self, *args, **kwargs):
        if self.return_ok:
            function = self.job_side_effect_ok
        else:
            function = self.job_side_effect_ko
        return function(*args, **kwargs)

    def job_side_effect_ok(self, *args, **kwargs):
        """Mock return of salt according to args."""
        minion = args[0]
        function = args[1]
        data = args[2]

        if function == 'remote_control.create_ssh_connection':
            return {'pid': 1234}

        return {}

    def job_side_effect_ko(self, *args, **kwargs):
        """Mock return of salt according to args."""
        minion = args[0]
        function = args[1]
        data = args[2]

        return {}

    @patch('projety.salt.Job.run')
    def test_remote_token(self, mock_job):
        """Test that the wsproxy send back data the way we want."""

        token = self.valid_token
        minion = self.valid_minion

        # Mock salt-job to return wanted data
        mock_job.side_effect = self.job_side_effect

        self.return_ok = True
        r, s, h = self.post(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 200
        assert 'token' in r

        self.return_ok = False
        r, s, h = self.post(
            '/api/v1.0/minions/{0}/remote'.format(minion),
            token_auth=token)
        assert s == 500
