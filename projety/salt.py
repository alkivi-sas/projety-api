"""Salt related code."""
from __future__ import absolute_import  # Because module name == salt

import logging

import salt.config
import salt.wheel
import salt.client

from .exceptions import ValidationError, SaltError

# Global salt variable
opts = salt.config.master_config('/etc/salt/master')
wheel = salt.wheel.WheelClient(opts)
client = salt.client.LocalClient(c_path='/etc/salt/master')

logger = logging.getLogger(__name__)

# Our app cache
minions = {}
functions = {}


def get_minions(type='minions', use_cache=True):
    """
    Build a cache using minions array.

    By default the type is minions and we use the cache
    """
    global minions
    if use_cache and type in minions:
        return minions[type]

    keys = wheel.cmd('key.list_all')
    if type not in keys:
        logger.warning('Unable to get {0} in keys'.format(type))
        raise SaltError('No key {0} in key.list_all'.format(type))
    minions[type] = keys[type]
    return minions[type]


def get_minion_functions(minion):
    """
    Build a cache using functions array.

    To get this we have to call sys.list_functions.
    And to call sys.list_functions we need a minion.
    We assume that the current machine is a minion, which should be
    the case everytile.
    """
    global functions
    if minion in functions:
        return functions[minion]

    # no functions, build cache
    job = Job()
    result = job.run(minion, 'sys.list_functions')
    functions[minion] = result

    return result


class Job(object):
    """Represents a Salt Job."""

    def __init__(self, only_one=True):
        """Keep trace of only_one to automatically raise error."""
        self.only_one = only_one

    def run(self, tgt, fun, arg=(), timeout=None, expr_form='glob', ret='',
            jid='', kwarg=None, **kwargs):
        """Run a basic task."""
        # Check if minion is valid
        if self.only_one:
            if tgt not in get_minions():
                msg = 'minion {0} is not valid'.format(tgt)
                logger.warning(msg)
                raise ValidationError(msg)

        result = client.cmd(tgt, fun,
                            arg=arg,
                            timeout=timeout,
                            expr_form=expr_form,
                            ret=ret,
                            jid=jid,
                            kwarg=kwarg,
                            **kwargs)

        # If only one, perform additional check
        if self.only_one:
            if tgt not in result:
                msg = 'minion {0} not in salt return'.format(tgt)
                logger.warning(msg)
                raise SaltError(msg)
            else:
                return result[tgt]
        return result
