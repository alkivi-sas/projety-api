"""All the tests of our project."""
import logging

import pytest

from projety import socketio
from utils import TestAPI

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('app_class')
class TestSocketIO(TestAPI):
    """Test for socketio."""

    def test_socketio(self):
        """Test several pings."""
        token = self.valid_token
        minion = self.valid_minion

        # First make async request to init celery
        r, s, h = self.post('/api/v1.0/tasks/ping', data={'target': [minion]},
                            token_auth=token)
        assert s == 200

        # check that we have the minion in keys
        assert minion in r

        # then start socketio
        client = socketio.test_client(self.app)
        client_bis = socketio.test_client(self.app)

        # clear old socket.io notifications
        client.get_received()
        client_bis.get_received()

        # ping a minion using socket.io
        client.emit('ping_minion', {'minion': minion}, token)

        # Check that we get to good value
        recvd = client.get_received()
        assert len(recvd) == 1
        assert recvd[0]['args'][0] == {minion: True}
        assert recvd[0]['name'] == 'job_result'

        # Check that client_bis dont get shit
        recvd = client_bis.get_received()
        assert len(recvd) == 0

        # Auth using socket.io
        client.emit('login', self.valid_user, self.valid_password)

        # Check that we get to good value
        recvd = client.get_received()
        assert len(recvd) == 1
        assert recvd[0]['name'] == 'login'
        assert 'token' in recvd[0]['args'][0]

        # Check that client_bis dont get shit
        recvd = client_bis.get_received()
        assert len(recvd) == 0

        # Wrong auth using socket.io
        client.emit('login', self.valid_user, 'toto')

        # Check that we get to good value
        recvd = client.get_received()
        assert len(recvd) == 1
        assert recvd[0]['name'] == 'login_error'
        assert 'error' in recvd[0]['args'][0]

        # Check that client_bis dont get shit
        recvd = client_bis.get_received()
        assert len(recvd) == 0
