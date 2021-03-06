"""All the tests of our project."""

import logging

from utils import TestAPI

logger = logging.getLogger(__name__)


class TestPing(TestAPI):
    """Test for users."""

    def test_ping_one(self):
        """Test basic ping access."""
        token = self.valid_token
        minion = self.valid_minion

        # we test both sync and async
        for url in ['/api/v1.0/ping/{0}'.format(minion),
                    '/api/v1.0/tasks/ping/{0}'.format(minion),
                    '/api/v1.0/minions/{0}/ping'.format(minion)]:
            # ping one minion
            r, s, h = self.post(url, token_auth=token)
            assert s == 200

            # check that we have the minion in keys
            assert minion in r

        # now invalid minion
        minion = 'invalid_minion_dzakdazdaz'
        for url in ['/api/v1.0/ping/{0}'.format(minion),
                    '/api/v1.0/tasks/ping/{0}'.format(minion),
                    '/api/v1.0/minions/{0}/ping'.format(minion)]:
            # ping one minion
            r, s, h = self.post(url, token_auth=token)
            assert s == 400

    def test_ping(self):
        """Test several pings."""
        token = self.valid_token
        minion = self.valid_minion

        # we test both sync and async
        for url in ['/api/v1.0/ping', '/api/v1.0/tasks/ping']:
            # ping using list
            r, s, h = self.post(url, data={'target': [minion]},
                                token_auth=token)
            assert s == 200
            assert minion in r

            # ping using scalar
            r, s, h = self.post(url, data={'target': minion},
                                token_auth=token)
            assert s == 200
            assert minion in r

            # ping using dict
            r, s, h = self.post(url, data={'target': {minion: 1}},
                                token_auth=token)
            assert s == 400

            # ping using list of valid and invalid minion
            r, s, h = self.post(url,
                                data={'target': [minion, 'minion_invalid']},
                                token_auth=token)
            assert s == 200
            assert minion in r

            # ping using scalar of invalid minion
            r, s, h = self.post(url, data={'target': 'minion_invalid'},
                                token_auth=token)
            assert s == 400

            # ping using list of invalid minion
            r, s, h = self.post(url, data={'target': ['minion_invalid']},
                                token_auth=token)
            assert s == 400
