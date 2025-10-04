"""
Request/Response Logging Middleware
Logs all API requests and responses with detailed information
"""

import logging
import json
import time
from flask import request, g
from functools import wraps
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_requests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ClearSkies_API')


class RequestLogger:
    """Middleware to log all API requests and responses"""

    @staticmethod
    def log_request():
        """Log incoming request details"""
        g.start_time = time.time()

        # Build request info
        request_info = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'headers': {
                'user-agent': request.headers.get('User-Agent'),
                'content-type': request.headers.get('Content-Type'),
                'authorization': 'Bearer ***' if request.headers.get('Authorization') else None
            }
        }

        # Log request body for POST requests
        if request.method == 'POST' and request.is_json:
            try:
                request_info['body'] = request.get_json()
            except Exception:
                request_info['body'] = 'Unable to parse JSON'

        logger.info(f"📥 INCOMING REQUEST: {json.dumps(request_info, indent=2)}")

    @staticmethod
    def log_response(response):
        """Log outgoing response details (without body)"""
        # Calculate request duration
        duration = time.time() - g.get('start_time', time.time())

        # Build response info (without body)
        response_info = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'path': request.path,
            'method': request.method
        }

        # Only log body size for large responses
        if response.is_json:
            try:
                response_data = response.get_json()
                response_str = json.dumps(response_data, indent=2)
                response_info['body_size_kb'] = round(len(response_str) / 1024, 2)
            except Exception:
                pass

        # Different log level based on status code
        if response.status_code >= 500:
            logger.error(f"📤 OUTGOING RESPONSE (ERROR): {json.dumps(response_info, indent=2)}")
        elif response.status_code >= 400:
            logger.warning(f"📤 OUTGOING RESPONSE (CLIENT ERROR): {json.dumps(response_info, indent=2)}")
        else:
            logger.info(f"📤 OUTGOING RESPONSE (SUCCESS): {json.dumps(response_info, indent=2)}")

        return response

    @staticmethod
    def log_error(error):
        """Log detailed error information"""
        error_info = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'path': request.path,
            'method': request.method,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }

        logger.error(f"❌ ERROR: {json.dumps(error_info, indent=2)}")


def log_api_call(func):
    """
    Decorator to log individual API endpoint calls
    Use this for specific endpoints that need detailed logging
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        endpoint_logger = logging.getLogger(f'API.{func.__name__}')

        # Log function entry
        endpoint_logger.info(f"🔧 Calling {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            endpoint_logger.info(f"✅ {func.__name__} completed successfully")
            return result
        except Exception as e:
            endpoint_logger.error(f"❌ {func.__name__} failed: {str(e)}")
            raise

    return wrapper


class StructuredLogger:
    """Structured logging for better parsing and analysis"""

    @staticmethod
    def log_dashboard_request(lat, lon, user_id=None):
        """Log dashboard API request"""
        log_entry = {
            'event': 'dashboard_request',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'location': {'latitude': lat, 'longitude': lon},
            'user_id': user_id,
            'ip': request.remote_addr
        }
        logger.info(f"📊 DASHBOARD: {json.dumps(log_entry)}")

    @staticmethod
    def log_data_source(source_name, success, data_points=0, error=None):
        """Log data source API call"""
        log_entry = {
            'event': 'data_source_call',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': source_name,
            'success': success,
            'data_points': data_points,
            'error': error
        }

        if success:
            logger.info(f"🔌 DATA SOURCE ({source_name}): {json.dumps(log_entry)}")
        else:
            logger.error(f"🔌 DATA SOURCE ERROR ({source_name}): {json.dumps(log_entry)}")

    @staticmethod
    def log_ai_summary(summary_type, tokens_used=0, duration_ms=0, success=True):
        """Log AI summary generation"""
        log_entry = {
            'event': 'ai_summary',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'type': summary_type,
            'tokens_used': tokens_used,
            'duration_ms': duration_ms,
            'success': success
        }
        logger.info(f"🤖 AI SUMMARY ({summary_type}): {json.dumps(log_entry)}")

    @staticmethod
    def log_cache_hit(endpoint, hit=True):
        """Log cache hit/miss"""
        log_entry = {
            'event': 'cache_access',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'endpoint': endpoint,
            'hit': hit
        }
        logger.info(f"💾 CACHE {'HIT' if hit else 'MISS'}: {json.dumps(log_entry)}")


# Export logger instances
request_logger = RequestLogger()
structured_logger = StructuredLogger()
