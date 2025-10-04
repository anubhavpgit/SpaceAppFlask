"""
ClearSkies API - Air Quality Intelligence Platform
Unified dashboard endpoint for React Native mobile app
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import os
from dotenv import load_dotenv

from config import config
from services import DashboardService
from auth import require_auth
from logger import request_logger, structured_logger, log_api_call

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = config.JSON_SORT_KEYS

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register request/response logging middleware
@app.before_request
def before_request():
    """Log all incoming requests"""
    request_logger.log_request()

@app.after_request
def after_request(response):
    """Log all outgoing responses"""
    return request_logger.log_response(response)

@app.errorhandler(Exception)
def handle_exception(error):
    """Log all exceptions"""
    request_logger.log_error(error)
    # Re-raise to let Flask handle it
    raise


def validate_location(func):
    """Validate latitude and longitude parameters"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = request.get_json() if request.is_json else {}

        lat = data.get('latitude')
        lon = data.get('longitude')

        if lat is None or lon is None:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_LOCATION',
                    'message': 'Latitude and longitude are required'
                }
            }), 400

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_LOCATION',
                    'message': 'Latitude and longitude must be valid numbers'
                }
            }), 400

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'OUT_OF_BOUNDS',
                    'message': 'Latitude must be between -90 and 90, longitude between -180 and 180'
                }
            }), 400

        kwargs['lat'] = lat
        kwargs['lon'] = lon
        return func(*args, **kwargs)

    return wrapper


# ============================================================================
# API Routes
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint with comprehensive system test
    Returns sample data for Midtown NYC to verify all services
    """
    import time
    start_time = time.time()

    # Midtown NYC coordinates
    MIDTOWN_NYC = {
        'latitude': 40.7549,
        'longitude': -73.9840,
        'name': 'Midtown Manhattan, NYC'
    }

    health_status = {
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '2.1.0',
        'environment': os.getenv('FLASK_ENV', 'production'),
        'services': {}
    }

    # Test data sources
    try:
        from services import TEMPOClient, OpenAQClient, OpenWeatherClient

        # Test NASA TEMPO
        tempo_start = time.time()
        tempo_data = TEMPOClient.get_air_quality(MIDTOWN_NYC['latitude'], MIDTOWN_NYC['longitude'])
        health_status['services']['tempo'] = {
            'status': 'operational' if tempo_data else 'degraded',
            'response_time_ms': int((time.time() - tempo_start) * 1000),
            'available': tempo_data is not None
        }

        # Test OpenAQ
        openaq_start = time.time()
        openaq_data = OpenAQClient.get_measurements(MIDTOWN_NYC['latitude'], MIDTOWN_NYC['longitude'])
        health_status['services']['openaq'] = {
            'status': 'operational' if openaq_data else 'degraded',
            'response_time_ms': int((time.time() - openaq_start) * 1000),
            'available': openaq_data is not None,
            'data_points': len(openaq_data) if openaq_data else 0
        }

        # Test OpenWeather
        weather_start = time.time()
        weather_data = OpenWeatherClient.get_weather(MIDTOWN_NYC['latitude'], MIDTOWN_NYC['longitude'])
        health_status['services']['weather'] = {
            'status': 'operational' if weather_data else 'degraded',
            'response_time_ms': int((time.time() - weather_start) * 1000),
            'available': weather_data is not None
        }

        # Test Gemini AI
        gemini_start = time.time()
        gemini_available = bool(os.getenv('GEMINI_API_KEY'))
        health_status['services']['gemini_ai'] = {
            'status': 'operational' if gemini_available else 'not_configured',
            'response_time_ms': int((time.time() - gemini_start) * 1000),
            'available': gemini_available
        }

    except Exception as e:
        health_status['services']['error'] = str(e)

    # Test dashboard endpoint with Midtown NYC data
    try:
        dashboard_start = time.time()
        dashboard_data = DashboardService.get_dashboard_data(
            MIDTOWN_NYC['latitude'],
            MIDTOWN_NYC['longitude']
        )
        dashboard_time = int((time.time() - dashboard_start) * 1000)

        health_status['test_location'] = MIDTOWN_NYC
        health_status['sample_data'] = {
            'dashboard_response_time_ms': dashboard_time,
            'current_aqi': dashboard_data.get('currentAQI', {}).get('raw', {}).get('aqi'),
            'data_completeness': dashboard_data.get('metadata', {}).get('dataCompleteness'),
            'sample_dashboard_data': dashboard_data  # Full dashboard data for Midtown NYC
        }

    except Exception as e:
        health_status['test_location'] = MIDTOWN_NYC
        health_status['sample_data'] = {
            'error': str(e)
        }

    # Overall status
    all_operational = all(
        service.get('status') == 'operational'
        for service in health_status['services'].values()
        if isinstance(service, dict)
    )

    health_status['overall_status'] = 'healthy' if all_operational else 'degraded'
    health_status['total_response_time_ms'] = int((time.time() - start_time) * 1000)

    return jsonify(health_status)


@app.route('/dashboard', methods=['POST'])
@require_auth
@validate_location
@log_api_call
def dashboard(lat: float, lon: float):
    """
    Unified Dashboard Endpoint

    Returns all necessary data for React Native dashboard:
    - Current air quality with AQI (raw + AI summary)
    - 24-hour forecast (raw + AI summary)
    - Health alerts (raw + AI summary)
    - Weather conditions (raw + AI summary)
    - Historical trends - 7 days (raw + AI summary)
    - Data source comparison (raw + AI summary)
    - Insights and personalized tips

    Request Body:
        {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "deviceId": "optional-device-id",
            "userPreferences": {
                "sensitiveGroup": false,
                "units": "metric"
            }
        }

    Headers:
        Authorization: Bearer <token>
    """
    try:
        import time
        start_time = time.time()

        # Log dashboard request
        user_data = request.get_json() or {}
        device_id = user_data.get('deviceId')
        structured_logger.log_dashboard_request(lat, lon, device_id)

        # Get comprehensive dashboard data
        dashboard_data = DashboardService.get_dashboard_data(lat, lon)

        # Update processing time
        processing_time = int((time.time() - start_time) * 1000)
        dashboard_data['metadata']['processingTime'] = processing_time

        # Log successful response
        structured_logger.log_ai_summary('dashboard_complete', 0, processing_time, True)

        response_data = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data': dashboard_data
        }

        # Log complete response for debugging
        print(f"\n{'='*80}")
        print(f"📤 COMPLETE API RESPONSE FOR ({lat}, {lon})")
        print(f"{'='*80}")
        import json
        print(json.dumps(response_data, indent=2))
        print(f"{'='*80}\n")

        return jsonify(response_data)

    except Exception as e:
        import traceback
        print(f"Dashboard error: {traceback.format_exc()}")
        request_logger.log_error(e)
        return jsonify({
            'success': False,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/api/air-quality/current', methods=['POST'])
@require_auth
@validate_location
def current_air_quality(lat: float, lon: float):
    """Get current air quality for a location"""
    try:
        data = DashboardService.get_current_air_quality(lat, lon)

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/api/forecast', methods=['POST'])
@require_auth
@validate_location
def forecast(lat: float, lon: float):
    """Get 24-hour air quality forecast"""
    try:
        hours = request.get_json().get('hours', 24)
        data = DashboardService.get_forecast(lat, lon, hours)

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/api/alerts', methods=['POST'])
@require_auth
@validate_location
def alerts(lat: float, lon: float):
    """Get health alerts for a location"""
    try:
        sensitive_group = request.get_json().get('sensitiveGroup', False)
        data = DashboardService.get_alerts(lat, lon, sensitive_group)

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


@app.route('/api/historical', methods=['POST'])
@require_auth
@validate_location
def historical(lat: float, lon: float):
    """Get historical air quality data with configurable period"""
    try:
        request_data = request.get_json() or {}
        period = request_data.get('period', '7d')

        # Map period string to days
        period_map = {
            '7d': 7,
            '30d': 30,
            '90d': 90
        }

        days = period_map.get(period, 7)
        data = DashboardService.get_historical(lat, lon, days)

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        }), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Endpoint not found'
        }
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500


if __name__ == '__main__':
    print(f"\n🌤️  ClearSkies API Starting...")
    print(f"📍 Listening on http://{config.HOST}:{config.PORT}")
    print(f"🔑 Auth: {'Enabled' if os.getenv('API_KEY') else 'Disabled (set API_KEY in .env)'}")
    print(f"🌍 Data Sources: NASA TEMPO, OpenAQ v3, OpenWeather")
    print(f"\n💡 Unified Dashboard: POST /api/dashboard")
    print(f"   Headers: Authorization: Bearer <token>")
    print(f"   Body: {{'latitude': 37.7749, 'longitude': -122.4194}}\n")

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
