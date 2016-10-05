"""Basic class for our test."""

import base64
import json
import pytest

from projety import db


@pytest.mark.usefixtures('client_class')
class TestAPI(object):
    """
    Generic class for our tests.

    It use the fixture client_class with allows us to self.client.
    """

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def setup(self):
        """Fixture for variable common in tests."""
        self._valid_token = None
        self._valid_minion = None
        self.valid_user = 'admin'
        self.valid_password = 'admin'
        self.admin_user = 'admin'
        self.admin_password = 'admin'
        self.restricted_user = 'restricted'
        self.restricted_password = 'restricted'

    @property
    def valid_token(self):
        """Get a token we know is valid."""
        if not self._valid_token:
            self._valid_token = self.get_valid_token(user=self.admin_user)
        return self._valid_token

    @property
    def valid_minion(self):
        """Get a minion on the current salt master."""
        if not self._valid_minion:
            r, s, h = self.get('/api/v1.0/minions',
                               token_auth=self.valid_token)
            self._valid_minion = r[0]
        return self._valid_minion

    def get_valid_token(self, user, password=None):
        """Return a valid token for a user."""
        if not password:
            password = user
        r, s, h = self.post('/api/v1.0/tokens',
                            basic_auth='{0}:{1}'.format(user, password))
        assert s == 200
        return r['token']

    def get_headers(self, basic_auth=None, token_auth=None):
        """Helper to get manage headers for requests."""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if basic_auth is not None:
            headers['Authorization'] = 'Basic ' + base64.b64encode(
                basic_auth.encode('utf-8')).decode('utf-8')
        if token_auth is not None:
            headers['Authorization'] = 'Bearer ' + token_auth
        return headers

    def get(self, url, basic_auth=None, token_auth=None):
        """Method to get."""
        rv = self.client.get(url,
                             headers=self.get_headers(basic_auth, token_auth))
        # clean up the database session, since this only occurs when the app
        # context is popped.
        db.session.remove()
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers

    def post(self, url, data=None, basic_auth=None, token_auth=None):
        """Method to post."""
        d = data if data is None else json.dumps(data)
        rv = self.client.post(url, data=d,
                              headers=self.get_headers(basic_auth, token_auth))
        # clean up the database session, since this only occurs when the app
        # context is popped.
        db.session.remove()
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers

    def put(self, url, data=None, basic_auth=None, token_auth=None):
        """Method to put."""
        d = data if data is None else json.dumps(data)
        rv = self.client.put(url, data=d,
                             headers=self.get_headers(basic_auth, token_auth))
        # clean up the database session, since this only occurs when the app
        # context is popped.
        db.session.remove()
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers

    def delete(self, url, basic_auth=None, token_auth=None):
        """Method to delete."""
        rv = self.client.delete(url, headers=self.get_headers(basic_auth,
                                                              token_auth))
        # clean up the database session, since this only occurs when the app
        # context is popped.
        db.session.remove()
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers
