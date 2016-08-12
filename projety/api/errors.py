"""Custom handles of API errors."""

from flask import jsonify
from ..exceptions import ValidationError
from . import api


@api.errorhandler(ValidationError)
def bad_request(e):
    """Send error 400 on ValidationError."""
    response = jsonify({'status': 400, 'error': 'bad request',
                        'message': e.args[0]})
    response.status_code = 400
    return response
