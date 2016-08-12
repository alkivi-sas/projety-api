"""Handles /keys endpoints."""
import logging

from flask import abort, request, jsonify

from ..salt import wheel, client
from ..auth import token_auth
from . import api

logger = logging.getLogger(__name__)


@api.route('/v1.0/ping/<minion>', methods=['POST'])
@token_auth.login_required
def ping_one(minion):
    """Return a simple test.ping."""
    all_keys = wheel.cmd('key.list_all')
    keys = all_keys['minions']
    if minion not in keys:
        abort(404)

    logger.debug('going to ping {0}'.format(minion))

    result = client.cmd(minion, 'test.ping')
    return jsonify(result)


@api.route('/v1.0/ping', methods=['POST'])
@token_auth.login_required
def ping():
    """Return the list of salt keys."""
    data = request.json
    targets = data['target']

    all_keys = wheel.cmd('key.list_all')
    keys = all_keys['minions']

    minions = []
    for m in targets:
        logger.debug('test {0}'.format(m))
        if m in keys:
            minions.append(m)

    if not minions:
        abort(404)

    real_target = ','.join(minions)
    logger.debug('Going to ping {0} as a list'.format(real_target))
    result = client.cmd(real_target, 'test.ping', expr_form='list')
    return jsonify(result)
