"""All the tests of our project."""

from utils import TestAPI


class TestTasks(TestAPI):
    """Test for tasks."""

    def test_tasks(self):
        """Test the structure of return of the salt tasks."""
        r, s, h = self.get('/api/v1.0/tasks', token_auth=self.valid_token)
        assert s == 200
        for subkeys in ['test.ping', 'state.sls']:
            assert subkeys in r
