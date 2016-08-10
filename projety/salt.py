"""Salt related code."""

from __future__ import absolute_import  # Because module name == salt

import salt.config
import salt.wheel
import salt.client

# Global salt variable
opts = salt.config.master_config('/etc/salt/master')
wheel = salt.wheel.WheelClient(opts)
client = salt.client.LocalClient()
