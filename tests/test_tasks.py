"""All the tests of our project."""

from utils import TestAPI


class TestTasks(TestAPI):
    """Test for users."""

    def test_async_ping_one(self):
        """Test basic ping access."""
        token = self.valid_token
        minion = self.valid_minion

        # ping one minion
        r, s, h = self.post('/api/v1.0/tasks/ping/{0}'.format(minion),
                            token_auth=token)
        assert s == 202

        url = h['Location']

        # wait for asnychronous task to complete
        while True:
            r, s, h = self.get(url)
            if s != 202:
                break
        assert s == 200

        # check that we have the minion in keys
        assert 'ping' in r
        assert minion in r['ping']

    def test_async_ping(self):
        """Test several pings."""
        token = self.valid_token
        minion = self.valid_minion

        r, s, h = self.post('/api/v1.0/tasks/ping', data={'target': [minion]},
                            token_auth=token)
        assert s == 202

        url = h['Location']

        # wait for asnychronous task to complete
        while True:
            r, s, h = self.get(url)
            if s != 202:
                break
        assert s == 200

        # check that we have the minion in keys
        assert 'ping' in r
        assert minion in r['ping']
