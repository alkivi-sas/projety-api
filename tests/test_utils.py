"""All the tests of our project."""
import logging
import os

from utils import TestAPI
from projety.utils import (get_open_port,
                           get_ssh_host_key_fingerprint)

logger = logging.getLogger(__name__)


class TestAsync(TestAPI):
    """Test for users."""

    def test_utils(self):
        """Test basic ping access."""
        port = get_open_port()
        assert port > 1024

        key = os.path.join(os.getcwd(), 'tests/test_key.pub')
        fingerprint = get_ssh_host_key_fingerprint(key)
        assert fingerprint == '85:fb:c5:da:b8:cb:01:3b:52:39:89:f7:9a:6d:34:5f'
