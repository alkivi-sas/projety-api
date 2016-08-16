"""Handles /keys endpoints."""
from flask import jsonify

from ..salt import wheel
from ..auth import token_auth
from . import api


@api.route('/v1.0/keys', methods=['GET'])
@token_auth.login_required
def get_keys():
    """
    Return the list of salt keys.

    ---
    tags:
      - keys
    security:
      - token: []
    responses:
      200:
        description: Returns the lists of keys
        schema:
          id: keys
          required:
            - local
            - minions
            - minions_denied
            - minions_pre
            - minions_rejected
          properties:
            local:
              type: array
              items:
                type: strings
            minions:
              type: array
              items:
                type: strings
            minions_denied:
              type: array
              items:
                type: strings
            minions_pre:
              type: array
              items:
                type: strings
            minions_rejected:
              type: array
              items:
                type: strings
    """
    keys = wheel.cmd('key.list_all')
    return jsonify(keys)
