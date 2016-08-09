"""Handles /keys endpoints."""
from flask import jsonify

from ..auth import token_auth
from . import api

import salt.config
import salt.wheel

opts = salt.config.master_config('/etc/salt/master')
wheel = salt.wheel.WheelClient(opts)


@api.route('/v1.0/keys', methods=['GET'])
@token_auth.login_required
def get_keys():
    """Return the list of salt keys."""
    keys = wheel.cmd('key.list_all')
    return jsonify({'keys': keys})
