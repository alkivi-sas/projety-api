"""Salt related code."""
from __future__ import absolute_import  # Because module name == salt

import logging

import salt.config
import salt.wheel
import salt.client

# Global salt variable
opts = salt.config.master_config('/etc/salt/master')
wheel = salt.wheel.WheelClient(opts)
client = salt.client.LocalClient(c_path='/etc/salt/master')

logger = logging.getLogger(__name__)

# Cache for functions in salt
functions = []


def get_functions():
    """
    Build a cache using functions array.

    To get this we have to call sys.list_functions.
    And to call sys.list_functions we need a minion.
    We assume that the current machine is a minion, which should be
    the case everytile.
    """
    global functions
    if functions:
        return functions

    # no functions, build cache
    caller = salt.client.Caller()
    functions = caller.cmd('sys.list_functions')
    return functions


class Job(object):
    """Represents a Salt Job."""

    def run(self, tgt, fun, arg=(), timeout=None, expr_form='glob', ret='',
            jid='', kwarg=None, **kwargs):
        """Run a basic task."""
        result = client.cmd(tgt, fun,
                            arg=arg,
                            timeout=timeout,
                            expr_form=expr_form,
                            ret=ret,
                            jid=jid,
                            kwarg=kwarg,
                            **kwargs)
        return result
