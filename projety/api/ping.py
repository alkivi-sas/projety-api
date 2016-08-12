"""Handles /keys endpoints."""
import logging

from flask import abort, request, jsonify

from ..exceptions import ValidationError
from ..salt import wheel, client
from ..auth import token_auth
from . import api
from .async import async

logger = logging.getLogger(__name__)


def _ping_one(minion):
    """Return a simple test.ping."""
    all_keys = wheel.cmd('key.list_all')
    keys = all_keys['minions']
    if minion not in keys:
        abort(404)

    logger.debug('going to ping {0}'.format(minion))
    result = client.cmd(minion, 'test.ping')
    return jsonify(result)


def _ping():
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

    all_keys = wheel.cmd('key.list_all')
    keys = all_keys['minions']

    minions = []
    for m in to_test:
        if m in keys:
            minions.append(m)

    if not minions:
        abort(404)

    real_target = ','.join(minions)
    logger.debug('Going to ping {0} as a list'.format(real_target))
    result = client.cmd(real_target, 'test.ping', expr_form='list')
    return jsonify(result)


@api.route('/v1.0/ping/<minion>', methods=['POST'])
@token_auth.login_required
def ping_one(minion):
    """Perform synchronous test.ping."""
    return _ping_one(minion)


@api.route('/v1.0/ping', methods=['POST'])
@token_auth.login_required
def ping():
    """Perform synchronous test.ping for a list."""
    return _ping()


@api.route('/v1.0/tasks/ping/<minion>', methods=['POST'])
@async
@token_auth.login_required
def async_ping_one(minion):
    """Perform asynchronous test.ping."""
    return _ping_one(minion)


@api.route('/v1.0/tasks/ping', methods=['POST'])
@async
@token_auth.login_required
def async_ping():
    """Perform asynchronous test.ping for a list."""
    return _ping()
