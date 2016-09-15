"""All the tests of our project."""
import logging

import pytest

from projety import socketio
from utils import TestAPI

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('app_class')
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

        # Normal result
        r, s, h = self.get('/api/v1.0/minions/{0}/tasks'.format(minion),
                           token_auth=token)
        assert s == 200
        assert isinstance(r, list)

        # Wrong minion result
        r, s, h = self.get('/api/v1.0/minions/{0}/tasks'.format('fzafazz'),
                           token_auth=token)
        assert s == 400

    def test_get_task_description(self):
        """Test the structure of return of the salt minions."""
        token = self.valid_token
        minion = self.valid_minion

        # Normal result
        r, s, h = self.get('/api/v1.0/minions/{0}/tasks/{1}'.format(minion,
                           'test.ping'), token_auth=token)
        assert s == 200
        assert 'documentation' in r

        # Wrong minion result
        r, s, h = self.get('/api/v1.0/minions/{0}/tasks/{1}'.format('fzafazz',
                           'test.ping'), token_auth=token)
        assert s == 400

        # Wrong task result
        r, s, h = self.get('/api/v1.0/minions/{0}/tasks/{1}'.format(minion,
                           'dzadazdazda.ping'), token_auth=token)
        assert s == 400

    def test_get_task_post(self):
        """Test the structure of return of the salt minions."""
        token = self.valid_token
        minion = self.valid_minion

        # Normal result
        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.ping')
        data = {'async': 'sync'}
        r, s, h = self.post(url, data=data, token_auth=token)
        assert s == 200
        assert minion in r

        # Async
        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.ping')
        data = {'async': 'async'}
        r, s, h = self.post(url, data=data, token_auth=token)
        assert s == 200
        assert minion in r

        # Test socketio
        client = socketio.test_client(self.app)
        client_bis = socketio.test_client(self.app)
        sid = client.sid

        # Clear socket.io
        client.get_received()
        client_bis.get_received()

        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.ping')
        data = {'async': 'socket.io', 'sid': sid}
        r, s, h = self.post(url, data=data, token_auth=token)
        assert s == 200
        assert 'jid' in r
        jid = r['jid']

        recvd = client.get_received()
        assert len(recvd) == 1
        assert recvd[0]['name'] == 'job_result'
        assert 'status' in recvd[0]['args'][0]
        assert 'jid' in recvd[0]['args'][0]
        assert 'result' in recvd[0]['args'][0]
        assert recvd[0]['args'][0]['jid'] == jid
        assert minion in recvd[0]['args'][0]['result']

        # Check that client_bis dont get shit
        recvd = client_bis.get_received()
        assert len(recvd) == 0

    def test_get_task_post_error(self):
        """Test the structure of return of the salt minions."""
        token = self.valid_token
        minion = self.valid_minion

        # Error task
        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.pingd')
        data = {'async': 'sync'}
        r, s, h = self.post(url, data=data, token_auth=token)
        assert s == 400

        # Error async
        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.ping')
        data = {'async': 'ssync'}
        r, s, h = self.post(url, data=data, token_auth=token)
        assert s == 400

        # Error socket.io not sid
        url = '/api/v1.0/minions/{0}/tasks/{1}'.format(minion, 'test.ping')
        data = {'async': 'socket.io'}
        r, s, h = self.post(url, data=data, token_auth=token)
        assert s == 400
