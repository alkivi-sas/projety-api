"""Custom handles of API errors."""

from flask import jsonify
from ..exceptions import ApiError
from . import api


@api.errorhandler(ApiError)
def bad_request(e):
    """Send error 400 on ValidationError."""
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response
