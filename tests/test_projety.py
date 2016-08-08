"""All the tests of our project."""

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

    def test_users(self):
        """Test user access with or without token."""
        # get users without auth
        r, s, h = self.get('/api/v1.0/users')
        assert s == 401

        # get users with bad auth
        r, s, h = self.get('/api/v1.0/users', token_auth='bad-token')
        assert s == 401

        # request a token with wrong password
        r, s, h = self.post('/api/v1.0/tokens', basic_auth='alkivi:toto')
        assert s == 401

        # request a token
        r, s, h = self.post('/api/v1.0/tokens', basic_auth='alkivi:alkivi123')
        assert s == 200
        token = r['token']
        print token

        # get users with good token
        r, s, h = self.get('/api/v1.0/users', token_auth=token)
        assert s == 200

        # revoke token
        r, s, h = self.delete('/api/v1.0/tokens', token_auth=token)
        assert s == 204

        # use invalid token
        r, s, h = self.get('/api/v1.0/users', token_auth=token)
        assert s == 401
