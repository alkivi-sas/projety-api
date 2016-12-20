"""Salt related code."""
from __future__ import absolute_import  # Because module name == salt

import logging

import salt.config
import salt.wheel
import salt.client
import salt.runner
import salt.utils.minions

from flask import request, g
from .exceptions import (ValidationError, SaltMinionError, SaltError,
                         SaltACLError)

# Global salt variable
opts = salt.config.master_config('/etc/salt/master')

logger = logging.getLogger(__name__)

# Our app cache
minions = {}
functions = {}


def ping_one(minion):
    """Return a simple test.ping."""
    job = Job()
    result = job.run(minion, 'test.ping')
    if not result:
        result = False
    return {minion: result}


def ping():
    """Return the simple test.ping but can be on a list."""
    data = request.json
    if not data:
        raise ValidationError('no json data in request')

    if 'target' not in data:
        raise ValidationError('no target in parameters')
    targets = data['target']

    to_test = None
    if isinstance(targets, list):
        to_test = targets
    elif isinstance(targets, (str, unicode)):
        to_test = [targets]
    else:
        raise ValidationError('target parameter is not an array not a scalar')

    keys = get_minions()
    minions = []
    for m in to_test:
        if m in keys:
            minions.append(m)

    if not minions:
        raise ValidationError('minions list is not valid')

    real_target = ','.join(minions)
    job = Job(only_one=False)
    result = job.run(real_target, 'test.ping', expr_form='list')
    return result


def get_minions(type='minions', use_cache=True):
    """
    Build a cache using minions array.

    By default the type is minions and we use the cache
    """
    global minions
    if use_cache and type in minions:
        return minions[type]

    wheel = salt.wheel.WheelClient(opts)
    keys = wheel.cmd('key.list_all')
    if type not in keys:
        raise SaltError('no key {0} in key.list_all'.format(type))
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


def is_task_allowed(tgt, fun, arg, tgt_type):
    """
    Check weither if the current user is allowed to run a task.

    Will be extended later.
    """
    if not g.current_user:
        logger.warning('This is weird, we should have a user here.')
        raise SaltACLError(tgt, fun, arg)

    checker = salt.utils.minions.CkMinions(opts)
    auth_list = g.current_user.get_salt_acl()
    logger.debug('auth_list for {0}'.format(g.current_user.nickname))
    logger.debug(auth_list)
    logger.debug('fun {0} tgt {1}'.format(fun, tgt))
    data = {
        'auth_list': auth_list,
        'funs': str(fun),
        'args': arg,
        'tgt': str(tgt),
        'tgt_type': tgt_type}
    return checker.auth_check(**data)

    # if task not in ['test.ping', 'sys.doc', 'sys.list_functions',
    #                 'remote_control.create_ssh_connection',
    #                 'remote_control.close_ssh_connection']:
    #     raise SaltACLError(task)


class Job(object):
    """Represents a Salt Job."""

    def __init__(self, only_one=True, async=False, bypass_check=False):
        """Keep trace of only_one to automatically raise error."""
        self.only_one = only_one
        self.async = async
        self.bypass_check = bypass_check

    def run(self, tgt, fun, arg=(), timeout=None, expr_form='glob', ret='',
            jid='', kwarg=None, **kwargs):
        """
        Run a basic task.

        In only_one mode, we perform some checks :
        - minion should be in the list, raise ValidationError if not
        - result should have a minion entrie, raise SaltMinionError if not
        """
        # Perform additional check
        if self.only_one:
            if tgt not in get_minions():
                msg = 'Minion {0} is not valid'.format(tgt)
                raise ValidationError(msg)

            # We skip check for sys.list_functions to infinite recursion
            if fun not in 'sys.list_functions':
                if fun not in get_minion_functions(tgt):
                    msg = 'Task {0} not valid'.format(fun)
                    raise ValidationError(msg)

        # Check ACL check
        if not self.bypass_check:
            good = is_task_allowed(tgt, fun, arg, expr_form)
            if not good:
                raise SaltACLError(tgt, fun, arg, expr_form)

        # We might want to run async request
        function = None
        client = salt.client.get_local_client()
        if self.async:
            function = client.cmd_async
        else:
            function = client.cmd

        info = 'launching {0} on {1}, '.format(fun, tgt) + \
               'using args {0}, '.format(str(arg)) + \
               'targeting using {0}'.format(expr_form)
        logger.info(info)
        result = function(tgt, fun,
                          arg=arg,
                          timeout=timeout,
                          expr_form=expr_form,
                          ret=ret,
                          jid=jid,
                          kwarg=kwarg,
                          **kwargs)

        logger.debug('result is {0}'.format(result))
        if self.async:
            return result

        # If only one, perform additional check
        if self.only_one:
            if tgt not in result:
                raise SaltMinionError(tgt)
            else:
                return result[tgt]
        return result
