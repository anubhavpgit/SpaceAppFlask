"""
Authentication middleware for ClearSkies API
"""

from flask import request, jsonify
from functools import wraps
import os


def require_auth(f):
    """
    Decorator to require authentication via Bearer token

    Expects header: Authorization: Bearer <token>
    Token should match API_KEY environment variable
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from environment
        api_key = os.getenv('API_KEY')

        # If no API_KEY is set, allow all requests (development mode)
        if not api_key:
            return f(*args, **kwargs)

        # Get Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_AUTH',
                    'message': 'Authorization header is required'
                }
            }), 401

        # Parse Bearer token
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_AUTH',
                    'message': 'Authorization header must be: Bearer <token>'
                }
            }), 401

        token = parts[1]

        # Validate token
        if token != api_key:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid authentication token'
                }
            }), 401

        return f(*args, **kwargs)

    return decorated_function
