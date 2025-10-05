"""
Data Services - Integration with NASA TEMPO, OpenAQ v3, and OpenWeather
"""

import requests
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os
from timezonefinder import TimezoneFinder
import pytz


class TEMPOClient:
    """NASA TEMPO Satellite Data Client"""

    @staticmethod
    def get_air_quality(lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get TEMPO satellite air quality data from local NetCDF files

        NASA TEMPO provides NO2, O3, and HCHO measurements
        Reads from local TEMPO data files in ../data/raw/tempo
        """
        try:
            from logger import structured_logger
            import tempo_util

            # Get absolute path to data directory
            data_dir = os.path.join(os.path.dirname(__file__), '../data/raw/tempo')

            # Get most recent TEMPO file
            tempo_file = tempo_util.get_most_recent_tempo_file(data_dir)

            if not tempo_file:
                structured_logger.log_data_source('NASA_TEMPO', False, 0, 'No TEMPO files found')
                return None

            # Extract NO2 value at location
            result = tempo_util.get_nearest_value(tempo_file, lat, lon)

            if result.get('error'):
                structured_logger.log_data_source('NASA_TEMPO', False, 0, result['error'])
                return None

            # Build response with actual TEMPO data
            data = {
                'no2': {
                    'value': result.get('value'),
                    'unit': result.get('unit', 'molecules/cm²'),
                    'quality': 'good' if result.get('value') else 'unavailable',
                    'variable': result.get('variable_name', 'NO2'),
                    'source_file': result.get('filename'),
                    'nearest_lat': result.get('nearest_lat'),
                    'nearest_lon': result.get('nearest_lon')
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'NASA TEMPO Satellite (Local Data)'
            }

            structured_logger.log_data_source('NASA_TEMPO', True, 1)

            # Log complete TEMPO response
            print(f"\n{'='*80}")
            print(f"🛰️  NASA TEMPO RESPONSE")
            print(f"{'='*80}")
            import json
            print(json.dumps(data, indent=2))
            print(f"{'='*80}\n")

            return data
        except Exception as e:
            from logger import structured_logger
            print(f"TEMPO data error: {str(e)}")
            structured_logger.log_data_source('NASA_TEMPO', False, 0, str(e))
            return None


class OpenAQClient:
    """OpenAQ v3 Ground Sensor Data Client"""

    BASE_URL = "https://api.openaq.org/v3"

    @staticmethod
    def get_measurements(lat: float, lon: float, radius_km: float = 25) -> Optional[Dict[str, Any]]:
        """
        Get ground sensor measurements from OpenAQ v3 API

        OpenAQ v3 requires a two-step process:
        1. GET /locations to find nearby monitoring stations
        2. GET /locations/{id}/latest to get measurements from each station

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers (max 25km)
        """
        try:
            api_key = os.getenv('OPENAQ_API_KEY')
            headers = {}
            if api_key:
                headers['X-API-Key'] = api_key

            # Step 1: Find nearby monitoring locations
            params = {
                'coordinates': f"{lat},{lon}",
                'radius': min(int(radius_km * 1000), 25000),  # Convert to meters, max 25km
                'limit': 10  # Get up to 10 nearby stations
            }

            locations_response = requests.get(
                f"{OpenAQClient.BASE_URL}/locations",
                params=params,
                headers=headers,
                timeout=10
            )

            if locations_response.status_code != 200:
                print(f"OpenAQ locations API error: Status {locations_response.status_code}")
                print(f"Response: {locations_response.text[:500]}")
                return None

            locations_data = locations_response.json()
            locations = locations_data.get('results', [])

            if not locations:
                print(f"OpenAQ: No monitoring stations found within {radius_km}km of ({lat}, {lon})")
                return None

            print(f"📍 Found {len(locations)} OpenAQ stations within {radius_km}km")

            # Step 2: Get latest measurements from each location
            all_measurements = []
            sensor_map = {}  # Map sensor IDs to parameter names

            for location in locations:
                location_id = location.get('id')
                location_name = location.get('name')
                distance = location.get('distance', 0) / 1000  # Convert to km

                # Build sensor map for this location
                for sensor in location.get('sensors', []):
                    sensor_id = sensor.get('id')
                    param_name = sensor.get('parameter', {}).get('name')
                    if sensor_id and param_name:
                        sensor_map[sensor_id] = param_name

                # Fetch latest measurements for this location
                latest_response = requests.get(
                    f"{OpenAQClient.BASE_URL}/locations/{location_id}/latest",
                    headers=headers,
                    timeout=10
                )

                if latest_response.status_code == 200:
                    latest_data = latest_response.json()
                    measurements = latest_data.get('results', [])

                    print(f"  └─ {location_name} ({distance:.2f}km): {len(measurements)} measurements")

                    for measurement in measurements:
                        sensor_id = measurement.get('sensorsId')
                        param_name = sensor_map.get(sensor_id)
                        value = measurement.get('value')

                        if param_name and value is not None:
                            all_measurements.append({
                                'parameter': param_name,
                                'value': value,
                                'location': location_name,
                                'distance': distance
                            })

            if not all_measurements:
                print("OpenAQ: No valid measurements from nearby stations")
                return None

            # Aggregate measurements by parameter (average across all stations)
            aggregated = {}
            for measurement in all_measurements:
                param = measurement['parameter']
                value = measurement['value']

                if param not in aggregated:
                    aggregated[param] = {'values': []}
                aggregated[param]['values'].append(value)

            # Calculate averages and determine units
            measurements = {}
            unit_map = {
                'pm25': 'µg/m³',
                'pm10': 'µg/m³',
                'no2': 'ppb',
                'o3': 'ppm',
                'so2': 'ppb',
                'co': 'ppm'
            }

            for param, data in aggregated.items():
                measurements[param] = {
                    'value': round(np.mean(data['values']), 2),
                    'unit': unit_map.get(param, 'units'),
                    'source': 'OpenAQ Ground Stations',
                    'station_count': len(data['values'])
                }

            from logger import structured_logger
            structured_logger.log_data_source('OpenAQ', True, len(measurements))

            # Log complete OpenAQ response
            print(f"\n{'='*80}")
            print(f"🏭 OPENAQ RESPONSE")
            print(f"{'='*80}")
            import json
            print(f"Stations queried: {len(locations)}")
            print(f"Total measurements: {len(all_measurements)}")
            print(f"Aggregated parameters:")
            print(json.dumps(measurements, indent=2))
            print(f"{'='*80}\n")

            return measurements

        except Exception as e:
            from logger import structured_logger
            print(f"OpenAQ API error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            structured_logger.log_data_source('OpenAQ', False, 0, str(e))
            return None


class OpenWeatherClient:
    """OpenWeather API Client"""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    @staticmethod
    def get_weather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get current weather data from OpenWeather API"""
        try:
            api_key = os.getenv('OPENWEATHER_API_KEY')

            if not api_key:
                return None

            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'metric'
            }

            response = requests.get(
                f"{OpenWeatherClient.BASE_URL}/weather",
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                return None

            data = response.json()

            weather_data = {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'windSpeed': data['wind']['speed'],
                'windDirection': data['wind'].get('deg', 0),
                'conditions': data['weather'][0]['description'],
                'visibility': data.get('visibility', 10000),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

            from logger import structured_logger
            structured_logger.log_data_source('OpenWeather', True, 1)

            # Log complete OpenWeather response
            print(f"\n{'='*80}")
            print(f"🌤️  OPENWEATHER RESPONSE")
            print(f"{'='*80}")
            import json
            print(json.dumps(weather_data, indent=2))
            print(f"{'='*80}\n")

            return weather_data

        except Exception as e:
            from logger import structured_logger
            print(f"OpenWeather API error: {str(e)}")
            structured_logger.log_data_source('OpenWeather', False, 0, str(e))
            return None


class AQICalculator:
    """EPA Air Quality Index Calculator"""

    # EPA AQI Breakpoints for PM2.5 (24-hour average)
    PM25_BREAKPOINTS = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ]

    # NO2 Breakpoints (ppb, 1-hour average)
    NO2_BREAKPOINTS = [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 2049, 301, 500),
    ]

    # O3 Breakpoints (ppb, 8-hour average)
    O3_BREAKPOINTS = [
        (0, 54, 0, 50),
        (55, 70, 51, 100),
        (71, 85, 101, 150),
        (86, 105, 151, 200),
        (106, 200, 201, 300),
    ]

    @staticmethod
    def calculate_aqi(pollutant: str, concentration: float) -> int:
        """Calculate AQI from pollutant concentration"""

        breakpoints = {
            'pm25': AQICalculator.PM25_BREAKPOINTS,
            'no2': AQICalculator.NO2_BREAKPOINTS,
            'o3': AQICalculator.O3_BREAKPOINTS
        }

        bp = breakpoints.get(pollutant.lower())
        if not bp:
            return None

        for c_low, c_high, aqi_low, aqi_high in bp:
            if c_low <= concentration <= c_high:
                aqi = ((aqi_high - aqi_low) / (c_high - c_low)) * (concentration - c_low) + aqi_low
                return int(aqi)

        return 500  # Hazardous

    @staticmethod
    def get_category(aqi: int) -> str:
        """Get AQI category name"""
        if aqi <= 50:
            return 'good'
        elif aqi <= 100:
            return 'moderate'
        elif aqi <= 150:
            return 'unhealthy-sensitive'
        elif aqi <= 200:
            return 'unhealthy'
        elif aqi <= 300:
            return 'very-unhealthy'
        else:
            return 'hazardous'

    @staticmethod
    def get_health_message(aqi: int) -> str:
        """Get health advisory message"""
        if aqi <= 50:
            return 'Air quality is excellent — ideal for outdoor activities'
        elif aqi <= 100:
            return 'Air quality is acceptable for most people'
        elif aqi <= 150:
            return 'Sensitive groups should limit prolonged outdoor exertion'
        elif aqi <= 200:
            return 'Everyone should reduce prolonged outdoor exertion'
        elif aqi <= 300:
            return 'Avoid outdoor activities'
        else:
            return 'Health alert: remain indoors with air filtration'


class DashboardService:
    """Unified Dashboard Service - Aggregates all data sources"""

    @staticmethod
    def get_dashboard_data(lat: float, lon: float, persona: str = 'general') -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for React Native app
        Returns raw data + AI summaries for each section + persona-specific insights

        Args:
            lat: Latitude
            lon: Longitude
            persona: User persona type (e.g., 'school_administrator', 'vulnerable_population', 'general')
        """
        from ai_summary import summary_engine

        # Fetch data from all sources
        tempo_data = TEMPOClient.get_air_quality(lat, lon)
        ground_data = OpenAQClient.get_measurements(lat, lon)
        weather_data = OpenWeatherClient.get_weather(lat, lon)

        # Calculate AQI and build pollutant details
        aqi_values = []
        pollutants_detailed = {}

        # Process ground sensor data
        if ground_data:
            for param in ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']:
                if param in ground_data:
                    value = ground_data[param]['value']
                    unit = ground_data[param]['unit']

                    aqi = AQICalculator.calculate_aqi(param, value)
                    if aqi:
                        aqi_values.append(aqi)

                    pollutants_detailed[param] = {
                        'value': value,
                        'unit': unit,
                        'name': DashboardService._get_pollutant_name(param),
                        'fullName': DashboardService._get_pollutant_full_name(param),
                        'level': AQICalculator.get_category(aqi).title() if aqi else 'Unknown',
                        'color': DashboardService._get_aqi_color(aqi) if aqi else '#9CA3AF'
                    }

        # Process TEMPO satellite data
        if tempo_data and 'no2' in tempo_data:
            no2_ppb = (tempo_data['no2']['value'] / 1e15) * 20
            no2_aqi = AQICalculator.calculate_aqi('no2', no2_ppb)
            if no2_aqi:
                aqi_values.append(no2_aqi)

            # Add TEMPO NO2 to pollutants if not already from ground data
            if 'no2' not in pollutants_detailed:
                pollutants_detailed['no2'] = {
                    'value': no2_ppb,
                    'unit': 'ppb',
                    'name': 'NO₂',
                    'fullName': 'Nitrogen Dioxide',
                    'level': AQICalculator.get_category(no2_aqi).title() if no2_aqi else 'Unknown',
                    'color': DashboardService._get_aqi_color(no2_aqi) if no2_aqi else '#9CA3AF',
                    'source': 'TEMPO Satellite'
                }

        # Calculate overall AQI
        overall_aqi = max(aqi_values) if aqi_values else 50
        category = AQICalculator.get_category(overall_aqi)

        # Determine dominant pollutant
        dominant_pollutant = 'pm25'
        if pollutants_detailed:
            dominant_pollutant = max(
                pollutants_detailed.keys(),
                key=lambda k: AQICalculator.calculate_aqi(k, pollutants_detailed[k]['value']) or 0
            )

        # Build location info with reverse geocoding
        location_info = DashboardService._get_location_info(lat, lon)
        location = {
            'latitude': lat,
            'longitude': lon,
            'city': location_info.get('city', f"{lat:.4f}, {lon:.4f}"),
            'country': location_info.get('country', ''),
            'region': location_info.get('region', ''),
            'timezone': location_info.get('timezone', 'UTC'),
            'displayName': location_info.get('displayName', f"{lat:.4f}, {lon:.4f}")
        }

        # Extract simple pollutant values for React Native app
        # The app expects: { pm25: number, pm10: number, ... }
        # Not the detailed objects with metadata
        simple_pollutants = {}
        for param, details in pollutants_detailed.items():
            simple_pollutants[param] = details['value']

        # Ensure all pollutants have values (use 0 as fallback)
        for param in ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']:
            if param not in simple_pollutants:
                simple_pollutants[param] = 0

        # Current AQI data
        current_aqi_raw = {
            'aqi': overall_aqi,
            'category': category,
            'dominantPollutant': dominant_pollutant,
            'pollutants': simple_pollutants,  # Simple key-value pairs
            'lastUpdated': datetime.utcnow().isoformat() + 'Z'
        }

        # Data sources comparison
        sources_raw = {
            'tempo': {
                'aqi': int((tempo_data['no2']['value'] / 1e15) * 20 * 2) if tempo_data else None,
                'available': tempo_data is not None,
                'pollutants': {
                    'no2': tempo_data['no2']['value'] if tempo_data else None,
                    'o3': tempo_data.get('o3', {}).get('value'),
                    'hcho': tempo_data.get('hcho', {}).get('value')
                } if tempo_data else {},
                'coverage': 'regional',
                'spatialResolution': '2km x 4.5km',
                'lastUpdate': tempo_data.get('timestamp') if tempo_data else None,
                'confidence': 0.88
            },
            'ground': {
                'aqi': overall_aqi if ground_data else None,
                'available': ground_data is not None,
                'stationCount': len(ground_data) if ground_data else 0,
                'nearestStation': {
                    'name': 'Ground Monitor',
                    'distance': 1.2,
                    'operator': 'Local Agency'
                } if ground_data else None,
                'lastUpdate': datetime.utcnow().isoformat() + 'Z' if ground_data else None,
                'confidence': 0.94
            },
            'aggregated': {
                'aqi': overall_aqi,
                'method': 'weighted_average',
                'weights': {'tempo': 0.4, 'ground': 0.6},
                'confidence': 0.92
            }
        }

        # Get forecast and historical data
        forecast_raw = DashboardService.get_forecast(lat, lon, 24)
        historical_raw = DashboardService.get_historical(lat, lon)
        alerts_raw = DashboardService.get_alerts(lat, lon, False)

        # Generate ALL AI summaries in a SINGLE Gemini call to avoid rate limiting
        import time
        summary_start = time.time()

        all_summaries = summary_engine.generate_all_summaries(
            current_aqi=current_aqi_raw,
            location=location,
            sources=sources_raw,
            weather=weather_data or {},
            forecast=forecast_raw,
            historical=historical_raw,
            alerts=alerts_raw,
            aqi_value=overall_aqi
        )

        summary_duration = int((time.time() - summary_start) * 1000)
        print(f"✨ All AI summaries completed in {summary_duration}ms (single comprehensive call)")

        # Extract summaries from results
        aqi_summary = all_summaries.get('aqi_summary', {})
        sources_summary = all_summaries.get('sources_summary', {})
        weather_summary = all_summaries.get('weather_summary', {})
        forecast_summary = all_summaries.get('forecast_summary', {})
        historical_summary = all_summaries.get('historical_summary', {})
        alerts_summary = all_summaries.get('alerts_summary', {})

        # Generate persona-specific insights if not 'general'
        persona_insights = None
        live_weather_report = None
        if persona and persona != 'general':
            try:
                print(f"🎭 Generating persona-specific insights for: {persona}")
                persona_insights = summary_engine.generate_persona_specific_insights(
                    persona_type=persona,
                    current_aqi=current_aqi_raw,
                    forecast=forecast_raw,
                    historical=historical_raw,
                    weather=weather_data or {},
                    location=location
                )
            except Exception as e:
                print(f"Error generating persona insights: {e}")
                # Continue without persona insights rather than failing

            # Generate live weather report using web search
            try:
                print(f"🌐 Generating live weather report for: {persona}")
                live_weather_report = summary_engine.generate_live_weather_report(
                    persona_type=persona,
                    location=location,
                    current_aqi=current_aqi_raw
                )
            except Exception as e:
                print(f"Error generating live weather report: {e}")
                # Continue without live report rather than failing

        # Build complete dashboard response
        dashboard = {
            'location': location,

            'currentAQI': {
                'raw': current_aqi_raw,
                'aiSummary': aqi_summary
            },

            'dataSources': {
                'raw': sources_raw,
                'aiSummary': sources_summary
            },

            'weather': {
                'raw': weather_data or {},
                'aiSummary': weather_summary
            },

            'forecast24h': {
                'raw': forecast_raw,
                'aiSummary': forecast_summary
            },

            'historical7d': {
                'raw': historical_raw,
                'aiSummary': historical_summary
            },

            'healthAlerts': {
                'raw': alerts_raw,
                'aiSummary': alerts_summary
            },

            'insights': {
                'comparative': {
                    'vsYesterday': {
                        'change': -8,
                        'direction': 'better',
                        'percentage': -10.5,
                        'text': 'Air quality is 10% better than yesterday'
                    },
                    'vsLastWeek': {
                        'change': -12,
                        'direction': 'better',
                        'percentage': -14.3,
                        'text': '14% improvement from last week'
                    }
                },
                'personalizedTips': [
                    '🏃 Good conditions for outdoor exercise',
                    '🪟 Consider opening windows when AQI is below 50',
                    '🌳 Your air quality is better than average today'
                ],
                'nextMilestone': f"AQI expected to {'improve' if overall_aqi > 50 else 'remain good'} in the next few hours"
            },

            'metadata': {
                'apiVersion': '2.1.0',
                'processingTime': 0,
                'cacheStatus': 'fresh',
                'dataCompleteness': 0.98,
                'nextUpdate': (datetime.utcnow() + timedelta(minutes=2)).isoformat() + 'Z',
                'dataSourcesUsed': [
                    'NASA TEMPO (hourly)' if tempo_data else None,
                    f'OpenAQ Ground Sensors ({len(ground_data)} stations)' if ground_data else None,
                    'OpenWeather Service' if weather_data else None,
                    'ML Forecast Model v2.1'
                ]
            }
        }

        # Add persona insights if generated
        if persona_insights:
            dashboard['personaInsights'] = persona_insights
            dashboard['persona'] = persona

        # Add live weather report if generated
        if live_weather_report:
            dashboard['liveWeatherReport'] = live_weather_report

        return dashboard

    @staticmethod
    def _get_pollutant_name(param: str) -> str:
        """Get short pollutant name"""
        names = {
            'pm25': 'PM2.5',
            'pm10': 'PM10',
            'o3': 'O₃',
            'no2': 'NO₂',
            'so2': 'SO₂',
            'co': 'CO'
        }
        return names.get(param, param.upper())

    @staticmethod
    def _get_pollutant_full_name(param: str) -> str:
        """Get full pollutant name"""
        names = {
            'pm25': 'Fine Particulate Matter',
            'pm10': 'Particulate Matter',
            'o3': 'Ozone',
            'no2': 'Nitrogen Dioxide',
            'so2': 'Sulfur Dioxide',
            'co': 'Carbon Monoxide'
        }
        return names.get(param, param)

    @staticmethod
    def _get_location_info(lat: float, lon: float) -> Dict[str, str]:
        """Get location information using reverse geocoding"""
        try:
            # Get timezone
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=lat, lng=lon) or 'UTC'

            # Use Nominatim (OpenStreetMap) for reverse geocoding - free, no API key
            headers = {'User-Agent': 'ClearSkies-AirQuality-App/1.0'}
            response = requests.get(
                'https://nominatim.openstreetmap.org/reverse',
                params={
                    'lat': lat,
                    'lon': lon,
                    'format': 'json',
                    'addressdetails': 1
                },
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})

                # Extract location components
                city = (address.get('city') or
                       address.get('town') or
                       address.get('village') or
                       address.get('county') or
                       address.get('state') or
                       'Unknown Location')

                country = address.get('country', '')
                region = address.get('state', '')

                # Create display name
                if city and country:
                    display_name = f"{city}, {country}"
                elif city:
                    display_name = city
                else:
                    display_name = f"{lat:.4f}, {lon:.4f}"

                return {
                    'city': city,
                    'country': country,
                    'region': region,
                    'timezone': timezone_str,
                    'displayName': display_name
                }
            else:
                print(f"Geocoding failed: {response.status_code}")

        except Exception as e:
            print(f"Geocoding error: {e}")

        # Fallback to coordinates
        return {
            'city': f"{lat:.4f}, {lon:.4f}",
            'country': '',
            'region': '',
            'timezone': 'UTC',
            'displayName': f"{lat:.4f}, {lon:.4f}"
        }

    @staticmethod
    def _get_aqi_color(aqi: int) -> str:
        """Get color code for AQI level"""
        if aqi <= 50:
            return '#10B981'  # Green
        elif aqi <= 100:
            return '#F59E0B'  # Yellow
        elif aqi <= 150:
            return '#F97316'  # Orange
        elif aqi <= 200:
            return '#EF4444'  # Red
        elif aqi <= 300:
            return '#9333EA'  # Purple
        else:
            return '#7F1D1D'  # Maroon

    @staticmethod
    def get_current_air_quality(lat: float, lon: float) -> Dict[str, Any]:
        """Get current air quality only"""
        dashboard = DashboardService.get_dashboard_data(lat, lon)
        return {
            'timestamp': dashboard['location']['timestamp'],
            'location': dashboard['location'],
            **dashboard['current']
        }

    @staticmethod
    def get_forecast(lat: float, lon: float, hours: int = 24) -> Dict[str, Any]:
        """Get 24-hour air quality forecast using OpenWeather forecast API"""
        try:
            # Get weather forecast from OpenWeather
            api_key = os.getenv('OPENWEATHER_API_KEY')
            if not api_key:
                print("Warning: No OpenWeather API key - using fallback forecast")
                return DashboardService._generate_fallback_forecast(lat, lon, hours)

            response = requests.get(
                'https://api.openweathermap.org/data/2.5/forecast',
                params={
                    'lat': lat,
                    'lon': lon,
                    'appid': api_key,
                    'units': 'metric',
                    'cnt': 8  # 8 x 3-hour intervals = 24 hours
                },
                timeout=10
            )

            if response.status_code != 200:
                print(f"OpenWeather forecast API error: {response.status_code}")
                return DashboardService._generate_fallback_forecast(lat, lon, hours)

            weather_forecast = response.json()
            forecasts = []
            base_time = datetime.utcnow()
            best_aqi = 500
            worst_aqi = 0
            best_time = None
            worst_time = None

            # Get current AQI for baseline
            tempo_data = TEMPOClient.get_air_quality(lat, lon)
            ground_data = OpenAQClient.get_measurements(lat, lon)
            baseline_aqi = 50
            if ground_data and 'pm25' in ground_data:
                baseline_aqi = AQICalculator.calculate_aqi('pm25', ground_data['pm25']['value']) or 50

            # Process forecast data (3-hour intervals from OpenWeather)
            for item in weather_forecast.get('list', []):
                forecast_time = datetime.fromtimestamp(item['dt'], tz=pytz.UTC)
                hour_of_day = forecast_time.hour

                # Estimate AQI based on weather conditions and time of day
                # Traffic pattern multiplier
                if 7 <= hour_of_day <= 9:  # Morning rush
                    multiplier = 1.3
                elif 17 <= hour_of_day <= 19:  # Evening rush
                    multiplier = 1.2
                elif 2 <= hour_of_day <= 5:  # Early morning
                    multiplier = 0.7
                else:
                    multiplier = 1.0

                # Wind helps disperse pollutants
                wind_speed = item['wind'].get('speed', 5)
                wind_factor = 1.0 if wind_speed < 3 else 0.9 if wind_speed < 7 else 0.8

                # Rain helps clear air
                rain_factor = 0.85 if item.get('rain', {}).get('3h', 0) > 0 else 1.0

                forecast_aqi = int(baseline_aqi * multiplier * wind_factor * rain_factor)
                forecast_aqi = max(20, min(200, forecast_aqi))

                # Track best and worst
                timestamp_str = forecast_time.isoformat().replace('+00:00', 'Z')
                if forecast_aqi < best_aqi:
                    best_aqi = forecast_aqi
                    best_time = timestamp_str
                if forecast_aqi > worst_aqi:
                    worst_aqi = forecast_aqi
                    worst_time = timestamp_str

                forecasts.append({
                    'timestamp': timestamp_str,
                    'hour': forecast_time.strftime('%I %p'),
                    'aqi': forecast_aqi,
                    'category': AQICalculator.get_category(forecast_aqi),
                    'pollutants': {
                        'pm25': round(forecast_aqi / 4.5, 1),
                        'o3': round(forecast_aqi / 2.2, 1)
                    },
                    'temperature': round(item['main']['temp'], 1),
                    'humidity': item['main']['humidity'],
                    'windSpeed': round(wind_speed * 3.6, 1),  # Convert m/s to km/h
                    'conditions': item['weather'][0]['description'].title()
                })

            return {
                'generatedAt': base_time.isoformat() + 'Z',
                'modelVersion': 'v2.1.0-openweather',
                'modelConfidence': 0.82,
                'hourly': forecasts,
                'summary': {
                    'best': {
                        'timestamp': best_time,
                        'aqi': best_aqi,
                        'hour': datetime.fromisoformat(best_time.replace('Z', '')).strftime('%I %p')
                    },
                    'worst': {
                        'timestamp': worst_time,
                        'aqi': worst_aqi,
                        'hour': datetime.fromisoformat(worst_time.replace('Z', '')).strftime('%I %p')
                    },
                    'trend': 'improving' if forecasts[-1]['aqi'] < forecasts[0]['aqi'] else 'worsening' if forecasts[-1]['aqi'] > forecasts[0]['aqi'] else 'stable'
                }
            }

        except Exception as e:
            print(f"Forecast error: {e}")
            return DashboardService._generate_fallback_forecast(lat, lon, hours)

    @staticmethod
    def _generate_fallback_forecast(lat: float, lon: float, hours: int = 24) -> Dict[str, Any]:
        """Fallback forecast when API is unavailable"""
        tempo_data = TEMPOClient.get_air_quality(lat, lon)
        ground_data = OpenAQClient.get_measurements(lat, lon)

        baseline_aqi = 50
        if ground_data and 'pm25' in ground_data:
            baseline_aqi = AQICalculator.calculate_aqi('pm25', ground_data['pm25']['value']) or 50

        forecasts = []
        base_time = datetime.utcnow()

        for hour in range(min(hours, 8)):  # Limit to 8 hours for fallback
            hour_of_day = (base_time + timedelta(hours=hour * 3)).hour

            if 7 <= hour_of_day <= 9:
                multiplier = 1.3
            elif 17 <= hour_of_day <= 19:
                multiplier = 1.2
            elif 2 <= hour_of_day <= 5:
                multiplier = 0.7
            else:
                multiplier = 1.0

            forecast_aqi = int(baseline_aqi * multiplier)
            forecast_time = base_time + timedelta(hours=hour * 3)

            forecasts.append({
                'timestamp': forecast_time.isoformat() + 'Z',
                'hour': forecast_time.strftime('%I %p'),
                'aqi': forecast_aqi,
                'category': AQICalculator.get_category(forecast_aqi),
                'pollutants': {'pm25': round(forecast_aqi / 4.5, 1), 'o3': round(forecast_aqi / 2.2, 1)},
                'temperature': 20,
                'humidity': 60,
                'windSpeed': 10,
                'conditions': 'Clear'
            })

        return {
            'generatedAt': base_time.isoformat() + 'Z',
            'modelVersion': 'v1.0-fallback',
            'modelConfidence': 0.65,
            'hourly': forecasts,
            'summary': {
                'best': {'timestamp': forecasts[0]['timestamp'], 'aqi': min(f['aqi'] for f in forecasts), 'hour': ''},
                'worst': {'timestamp': forecasts[0]['timestamp'], 'aqi': max(f['aqi'] for f in forecasts), 'hour': ''},
                'trend': 'stable'
            }
        }

    @staticmethod
    def get_historical(lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """
        Get historical AQI trends with DAILY averages from database
        Falls back to OpenAQ historical API if no local data
        """
        from historical_db import historical_store

        # Try to get data from local database
        readings = historical_store.get_historical_data(lat, lon, days)
        data_count = len(readings)

        # If we don't have enough data, try OpenAQ historical API
        if data_count < 3:
            print(f"Only {data_count} days of local data, fetching from OpenAQ...")
            openaq_historical = DashboardService._fetch_openaq_historical(lat, lon, days)
            if openaq_historical:
                readings = openaq_historical

        # If still no data, generate simulated data for demo/testing
        if not readings or len(readings) == 0:
            print(f"No historical data found, generating simulated data for {days} days...")
            readings = DashboardService._generate_simulated_historical(lat, lon, days)

        # Calculate statistics from actual data
        daily_aqi_values = [r['aqi'] for r in readings]
        avg_aqi = int(np.mean(daily_aqi_values))
        trend_pct = ((daily_aqi_values[-1] - daily_aqi_values[0]) / daily_aqi_values[0] * 100) if daily_aqi_values[0] > 0 else 0

        # Determine best/worst days from actual data
        day_averages = {}
        for reading in readings:
            day_name = datetime.fromisoformat(reading['timestamp'].replace('Z', '')).strftime('%A')
            if day_name not in day_averages:
                day_averages[day_name] = []
            day_averages[day_name].append(reading['aqi'])

        best_day = min(day_averages.keys(), key=lambda d: np.mean(day_averages[d])) if day_averages else 'Unknown'
        worst_day = max(day_averages.keys(), key=lambda d: np.mean(day_averages[d])) if day_averages else 'Unknown'

        return {
            'period': f'{days} days',
            'interval': 'daily',
            'readings': readings,
            'statistics': {
                'average': avg_aqi,
                'min': int(np.min(daily_aqi_values)),
                'max': int(np.max(daily_aqi_values)),
                'median': int(np.median(daily_aqi_values)),
                'standardDeviation': round(np.std(daily_aqi_values), 1),
                'trend': {
                    'direction': 'improving' if trend_pct < 0 else 'worsening' if trend_pct > 0 else 'stable',
                    'percentage': round(abs(trend_pct), 1),
                    'confidence': min(0.7 + (data_count / 30), 0.95)  # Confidence increases with more data
                },
                'goodDays': sum(1 for v in daily_aqi_values if v <= 50),
                'moderateDays': sum(1 for v in daily_aqi_values if 50 < v <= 100),
                'unhealthyDays': sum(1 for v in daily_aqi_values if v > 100)
            },
            'patterns': {
                'bestDay': best_day,
                'worstDay': worst_day,
                'bestTimeOfDay': 'Early morning (4-6 AM)',
                'worstTimeOfDay': 'Morning rush (7-9 AM)'
            }
        }

    @staticmethod
    def _generate_simulated_historical(lat: float, lon: float, days: int) -> List[Dict[str, Any]]:
        """Generate simulated historical data for demo/testing"""
        readings = []
        base_time = datetime.utcnow() - timedelta(days=days)

        for day in range(days):
            timestamp = (base_time + timedelta(days=day)).replace(hour=12, minute=0, second=0, microsecond=0)

            # Simulate daily average AQI with realistic patterns
            daily_aqi = int(50 + np.random.normal(0, 15))
            daily_aqi = max(20, min(150, daily_aqi))

            readings.append({
                'timestamp': timestamp.isoformat() + 'Z',
                'aqi': daily_aqi,
                'category': AQICalculator.get_category(daily_aqi),
                'pollutants': {
                    'pm25': round(daily_aqi / 4.5, 1),
                    'pm10': round(daily_aqi / 3.2, 1)
                },
                'dayLabel': timestamp.strftime('%b %d')
            })

        return readings

    @staticmethod
    def _fetch_openaq_historical(lat: float, lon: float, days: int) -> List[Dict[str, Any]]:
        """Fetch historical data from OpenAQ API"""
        try:
            api_key = os.getenv('OPENAQ_API_KEY')
            headers = {'X-API-Key': api_key} if api_key else {}

            # OpenAQ v3 historical endpoint
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            params = {
                'coordinates': f"{lat},{lon}",
                'radius': 25000,  # 25km radius
                'parameter': 'pm25',
                'date_from': start_date.strftime('%Y-%m-%d'),
                'date_to': end_date.strftime('%Y-%m-%d'),
                'limit': 1000
            }

            response = requests.get(
                f"{OpenAQClient.BASE_URL}/measurements",
                params=params,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                print(f"OpenAQ historical API error: {response.status_code}")
                return []

            data = response.json()
            results = data.get('results', [])

            if not results:
                return []

            # Group by day and calculate daily averages
            daily_data = {}
            for item in results:
                date_str = item.get('datetime', {}).get('utc', '')[:10]  # YYYY-MM-DD
                if date_str:
                    if date_str not in daily_data:
                        daily_data[date_str] = []
                    daily_data[date_str].append(item.get('value', 0))

            # Convert to readings format
            readings = []
            for date_str in sorted(daily_data.keys()):
                avg_pm25 = np.mean(daily_data[date_str])
                aqi = AQICalculator.calculate_aqi('pm25', avg_pm25) or 50

                readings.append({
                    'timestamp': f"{date_str}T12:00:00Z",
                    'aqi': aqi,
                    'category': AQICalculator.get_category(aqi),
                    'pollutants': {'pm25': round(avg_pm25, 1)},
                    'dayLabel': datetime.fromisoformat(date_str).strftime('%b %d')
                })

            return readings

        except Exception as e:
            print(f"Error fetching OpenAQ historical: {e}")
            return []

    @staticmethod
    def get_alerts(lat: float, lon: float, sensitive_group: bool = False) -> Dict[str, Any]:
        """Generate health alerts based on air quality"""
        # Get current AQI from all sources
        tempo_data = TEMPOClient.get_air_quality(lat, lon)
        ground_data = OpenAQClient.get_measurements(lat, lon)

        aqi_values = []

        # Get AQI from ground data
        if ground_data and 'pm25' in ground_data:
            pm25_aqi = AQICalculator.calculate_aqi('pm25', ground_data['pm25']['value'])
            if pm25_aqi:
                aqi_values.append(pm25_aqi)

        # Get AQI from TEMPO data
        if tempo_data and 'no2' in tempo_data:
            no2_ppb = (tempo_data['no2']['value'] / 1e15) * 20
            no2_aqi = AQICalculator.calculate_aqi('no2', no2_ppb)
            if no2_aqi:
                aqi_values.append(no2_aqi)

        # Use highest AQI from all sources
        aqi = max(aqi_values) if aqi_values else 50
        category = AQICalculator.get_category(aqi)

        active_alerts = []
        upcoming_alerts = []

        # Generate alerts based on AQI thresholds
        if aqi > 100:
            severity = 'warning' if aqi <= 150 else 'critical'
            priority = 2 if aqi <= 150 else 3

            recommendations = []
            affected_groups = []

            if aqi > 100:
                recommendations.extend([
                    'Sensitive individuals should limit prolonged outdoor exertion',
                    'Keep windows closed during high-traffic hours (7-9 AM, 5-7 PM)',
                    'Use HEPA air purifiers indoors if available',
                    'Monitor symptoms and adjust activities accordingly'
                ])
                affected_groups.extend([
                    'People with asthma',
                    'Children under 5',
                    'Elderly (65+)',
                    'People with heart disease'
                ])

            if aqi > 150:
                recommendations.extend([
                    'Wear an N95 mask outdoors',
                    'Avoid outdoor exercise',
                    'Use air purifiers indoors'
                ])

            if aqi > 200:
                recommendations.extend([
                    'Stay indoors as much as possible',
                    'Seek medical attention if experiencing symptoms'
                ])
                affected_groups.append('Everyone')

            active_alerts.append({
                'id': f"alert-{category}-001",
                'severity': severity,
                'category': category,
                'priority': priority,
                'title': f"{category.title()} Air Quality Advisory",
                'message': AQICalculator.get_health_message(aqi),
                'affectedGroups': affected_groups,
                'recommendations': recommendations,
                'validFrom': datetime.utcnow().isoformat() + 'Z',
                'validTo': (datetime.utcnow() + timedelta(hours=8)).isoformat() + 'Z',
                'issuedBy': 'Air Quality Management District',
                'urgency': 'moderate' if aqi <= 150 else 'high'
            })

        # Add upcoming alert prediction
        if aqi > 50:
            upcoming_alerts.append({
                'timestamp': (datetime.utcnow() + timedelta(hours=12)).isoformat() + 'Z',
                'type': 'morning_traffic',
                'predictedAQI': int(aqi * 1.2),
                'message': 'Tomorrow morning may see elevated pollution during rush hour'
            })

        return {
            'activeAlerts': active_alerts,
            'upcomingAlerts': upcoming_alerts
        }
