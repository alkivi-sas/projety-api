"""All the tests of our project."""
import logging

import mock
import pytest

from projety.api.async import async
from utils import TestAPI

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('app_class')
class TestAsyncPing(TestAPI):
    """Test for celery."""

    def test_celery(self):
        """Several tests for celery base on flack tutorial."""
        # add an additional route used only in tests
        @self.app.route('/foo')
        @async
        def foo():
            1 / 0

        token = self.valid_token
        minion = self.valid_minion

        with mock.patch('projety.api.async.run_flask_request.apply_async',
                        return_value=mock.MagicMock(state='PENDING')) as m:
            r, s, h = self.post(
                '/api/v1.0/tasks/ping',
                data={'target': [minion]},
                token_auth=token)
            assert s == 202
            assert m.call_count == 1
            environ = m.call_args_list[0][1]['args'][0]
            logger.warning(environ)
            assert environ['_wsgi.input'] == b'{"target": ["%s"]}' % minion

        with mock.patch('projety.api.async.run_flask_request.apply_async',
                        return_value=mock.MagicMock(state='STARTED')) as m:
            r, s, h = self.post(
                '/api/v1.0/tasks/ping',
                data={'target': [minion]},
                token_auth=token)
            assert s == 202
            assert m.call_count == 1
            environ = m.call_args_list[0][1]['args'][0]
            logger.warning(environ)
            assert environ['_wsgi.input'] == b'{"target": ["%s"]}' % minion

        with mock.patch('projety.api.async.run_flask_request.apply_async',
                        return_value=mock.MagicMock(
                            state='SUCCESS',
                            info=('foo', 201, {'a': 'b'}))) as m:
            r, s, h = self.post(
                '/api/v1.0/tasks/ping',
                data={'target': [minion]},
                token_auth=token)
            assert s == 201
            assert r == 'foo'
            assert 'a' in h
            assert h['a'] == 'b'
            assert m.call_count == 1
            environ = m.call_args_list[0][1]['args'][0]
            assert environ['_wsgi.input'] == b'{"target": ["%s"]}' % minion
