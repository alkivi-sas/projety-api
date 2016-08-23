"""Custom handles of API errors."""

from flask import jsonify
from ..exceptions import ValidationError, SaltError
from . import api


@api.errorhandler(ValidationError)
def bad_request(e):
    """Send error 400 on ValidationError."""
    response = jsonify({'status': 400, 'error': 'bad request',
                        'message': e.args[0]})
    response.status_code = 400
    return response


@api.errorhandler(SaltError)
def bad_salt_result(e):
    """Send error 500 on SaltError."""
    response = jsonify({'status': 500, 'error': 'salt wrong return',
                        'message': e.args[0]})
    response.status_code = 500
    return response
