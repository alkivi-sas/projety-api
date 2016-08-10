"""Handle nice json response for error."""
import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def not_found(e):
    """Send a correct json for 404."""
    logger.warning('dnzajdnzajdnazjkdnazjkdnzakj')
    response = jsonify({'status': 404, 'error': 'not found',
                        'message': 'invalid resource URI'})
    response.status_code = 404
    return response


def method_not_supported(e):
    """Send a correct json for 405."""
    response = jsonify({'status': 405, 'error': 'method not supported',
                        'message': 'the method is not supported'})
    response.status_code = 405
    return response


def internal_server_error(e):
    """Send a correct json for 500."""
    response = jsonify({'status': 500, 'error': 'internal server error',
                        'message': e.args[0]})
    response.status_code = 500
    return response
