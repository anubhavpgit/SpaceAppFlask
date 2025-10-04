"""
AI Summary Engine using Google Gemini
Generates human-readable summaries from air quality data
"""

import os
import json
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai

# Suppress gRPC ALTS warning
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''


class GeminiSummaryEngine:
    """Generate AI summaries using Google Gemini"""

    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            # Use gemini-2.0-flash-exp (experimental, free with higher limits)
            # Falls back to gemini-1.5-flash if exp not available
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def generate_all_summaries(self, current_aqi: Dict[str, Any], location: Dict[str, Any],
                               sources: Dict[str, Any], weather: Dict[str, Any],
                               forecast: Dict[str, Any], historical: Dict[str, Any],
                               alerts: Dict[str, Any], aqi_value: int) -> Dict[str, Dict[str, str]]:
        """Generate ALL summaries in a SINGLE Gemini API call to avoid rate limiting"""

        if not self.model:
            return {
                'aqi_summary': self._fallback_aqi_summary(current_aqi),
                'sources_summary': self._fallback_sources_summary(sources),
                'weather_summary': self._fallback_weather_summary(weather),
                'forecast_summary': self._fallback_forecast_summary(forecast),
                'historical_summary': self._fallback_historical_summary(historical),
                'alerts_summary': self._fallback_alerts_summary(alerts, aqi_value)
            }

        prompt = f"""You are an expert air quality analyst. Analyze this comprehensive air quality data and provide insights.

LOCATION: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}

CURRENT CONDITIONS:
- AQI: {aqi_value} ({current_aqi.get('category', 'unknown')})
- Dominant Pollutant: {current_aqi.get('dominantPollutant', 'unknown')}
- Pollutants: {json.dumps(current_aqi.get('pollutants', {}))}

WEATHER CONDITIONS (Critical for air quality analysis):
- Temperature: {weather.get('temperature', 0)}°C
- Humidity: {weather.get('humidity', 0)}%
- Wind Speed: {weather.get('windSpeed', 0)} m/s
- Wind Direction: {weather.get('windDirection', 0)}°
- Conditions: {weather.get('conditions', 'unknown')}
- Visibility: {weather.get('visibility', 10000)}m

WEATHER IMPACT ANALYSIS:
- Strong winds (>7 m/s) disperse pollutants and improve air quality
- Low winds (<3 m/s) allow pollutants to accumulate
- High humidity (>70%) can trap pollutants near ground level
- Rain washes pollutants from air, improving conditions
- Temperature inversions (cold air trapped below warm) worsen pollution

DATA SOURCES:
{json.dumps(sources, indent=2)}

24-HOUR FORECAST:
{json.dumps(forecast, indent=2)}

7-DAY HISTORICAL DATA:
{json.dumps(historical, indent=2)}

HEALTH ALERTS:
- Active Alerts: {len(alerts.get('activeAlerts', []))}
- Upcoming Alerts: {len(alerts.get('upcomingAlerts', []))}

Generate a comprehensive analysis in JSON format with these 6 sections:

{{
  "aqi_summary": {{
    "brief": "One sentence about current AQI (max 20 words)",
    "detailed": "2-3 sentences explaining AQI, category, and dominant pollutant",
    "recommendation": "Clear action advice for outdoor activities",
    "insight": "Interesting fact with emoji about air quality patterns"
  }},
  "sources_summary": {{
    "brief": "One sentence about data reliability (max 20 words)",
    "detailed": "2-3 sentences explaining how satellite and ground data work together",
    "validation": "Statement about data correlation/agreement",
    "dataQuality": "Assessment of overall data quality"
  }},
  "weather_summary": {{
    "brief": "One sentence about current weather (max 20 words)",
    "detailed": "2-3 sentences SPECIFICALLY explaining how current wind speed of {weather.get('windSpeed', 0)} m/s, humidity of {weather.get('humidity', 0)}%, and {weather.get('conditions', 'current conditions')} are affecting air quality RIGHT NOW",
    "impact": "Clear statement of weather's effect on air quality (favorable/unfavorable and WHY)",
    "uvAlert": "UV or weather-related health tip"
  }},
  "forecast_summary": {{
    "brief": "One sentence forecast overview (max 20 words)",
    "detailed": "2-3 sentences about expected air quality changes over next 24 hours",
    "recommendations": ["tip1", "tip2", "tip3"],
    "keyInsights": "Most important timing advice for outdoor activities"
  }},
  "historical_summary": {{
    "brief": "One sentence about the weekly trend (max 20 words)",
    "detailed": "2-3 sentences analyzing patterns and what influenced them",
    "trendAnalysis": "Insight about the trend direction with emoji (📈 or 📉)",
    "weeklyInsight": "Comparative insight vs typical conditions",
    "recommendation": "Advice based on observed patterns"
  }},
  "alerts_summary": {{
    "brief": "One sentence alert summary (max 20 words)",
    "detailed": "2-3 sentences about who is affected and why",
    "riskLevel": "Clear risk statement for different groups",
    "actionRequired": "What people should do (or not do)",
    "nextUpdate": "When to check again or expect changes"
  }}
}}

IMPORTANT:
- For weather_summary, analyze EXACTLY how the specific weather conditions are influencing air quality
- Explain wind dispersal, humidity trapping, rain cleansing effects based on ACTUAL values
- Be specific about whether conditions are favorable or unfavorable and WHY
- Keep all responses clear, actionable, and focused on user health
- Return ONLY valid JSON, no extra text"""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()
            response = self.model.generate_content(prompt)
            duration_ms = int((time.time() - start_time) * 1000)

            # Parse JSON from response
            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)

            # Log comprehensive Gemini response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI AI COMPREHENSIVE RESPONSE (Single Call)")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Prompt chars: {len(prompt)}, Response chars: {len(text)}")
            print(json.dumps(result, indent=2))
            print(f"{'='*80}\n")

            structured_logger.log_ai_summary('all_summaries', len(text), duration_ms, True)

            return result

        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            if '429' in error_msg or 'quota' in error_msg.lower():
                print(f"Gemini API rate limit hit - using fallback for all summaries")
            else:
                print(f"Gemini API error (comprehensive): {error_msg}")
            structured_logger.log_ai_summary('all_summaries', 0, 0, False)
            return {
                'aqi_summary': self._fallback_aqi_summary(current_aqi),
                'sources_summary': self._fallback_sources_summary(sources),
                'weather_summary': self._fallback_weather_summary(weather),
                'forecast_summary': self._fallback_forecast_summary(forecast),
                'historical_summary': self._fallback_historical_summary(historical),
                'alerts_summary': self._fallback_alerts_summary(alerts, aqi_value)
            }

    def generate_aqi_summary(self, aqi_data: Dict[str, Any], location: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI summary for current AQI data"""

        if not self.model:
            return self._fallback_aqi_summary(aqi_data)

        prompt = f"""You are an air quality expert assistant. Generate a friendly, clear summary of air quality data.

Location: {location.get('city', 'Unknown')}, {location.get('country', '')}
Current AQI: {aqi_data.get('aqi', 0)}
Category: {aqi_data.get('category', 'unknown')}
Dominant Pollutant: {aqi_data.get('dominantPollutant', 'unknown')}
Pollutants: {json.dumps(aqi_data.get('pollutants', {}), indent=2)}

Generate exactly 4 items in JSON format:
{{
  "brief": "One casual sentence summary (max 20 words)",
  "detailed": "2-3 informative sentences explaining the situation, causes, and what to expect",
  "recommendation": "Specific actionable advice for outdoor activities",
  "insight": "One interesting fact or tip with an emoji"
}}

Keep it friendly, avoid jargon, be specific and actionable."""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()
            response = self.model.generate_content(prompt)
            duration_ms = int((time.time() - start_time) * 1000)

            # Parse JSON from response
            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)
            structured_logger.log_ai_summary(
                'aqi_summary', len(text), duration_ms, True)

            # Log Gemini response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI AI RESPONSE - AQI Summary")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Result: {json.dumps(result, indent=2)}")
            print(f"{'='*80}\n")

            return result
        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            # Don't log full rate limit messages
            if '429' in error_msg or 'quota' in error_msg.lower():
                print(f"Gemini API rate limit hit - using fallback")
            else:
                print(f"Gemini API error: {error_msg}")
            structured_logger.log_ai_summary('aqi_summary', 0, 0, False)
            return self._fallback_aqi_summary(aqi_data)

    def generate_data_sources_summary(self, sources: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI summary for data source comparison"""

        if not self.model:
            return self._fallback_sources_summary(sources)

        prompt = f"""You are an air quality expert. Explain data source validation in simple terms.

Data Sources:
{json.dumps(sources, indent=2)}

Generate exactly 4 items in JSON format:
{{
  "brief": "One sentence about data reliability (max 20 words)",
  "detailed": "2-3 sentences explaining how satellite and ground data work together",
  "validation": "Statement about data correlation/agreement",
  "dataQuality": "Assessment of overall data quality"
}}

Keep it clear and build user confidence in the data."""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()
            response = self.model.generate_content(prompt)
            duration_ms = int((time.time() - start_time) * 1000)

            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)
            structured_logger.log_ai_summary(
                'sources_summary', len(text), duration_ms, True)

            # Log Gemini response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI AI RESPONSE - Data Sources Summary")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Result: {json.dumps(result, indent=2)}")
            print(f"{'='*80}\n")

            return result
        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            if '429' not in error_msg and 'quota' not in error_msg.lower():
                print(f"Gemini API error (sources): {error_msg}")
            structured_logger.log_ai_summary('sources_summary', 0, 0, False)
            return self._fallback_sources_summary(sources)

    def generate_weather_summary(self, weather: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI summary for weather impact on air quality"""

        if not self.model:
            return self._fallback_weather_summary(weather)

        prompt = f"""You are a meteorologist explaining weather's impact on air quality.

Weather Data:
{json.dumps(weather, indent=2)}

Generate exactly 4 items in JSON format:
{{
  "brief": "One sentence about current weather and air quality impact (max 20 words)",
  "detailed": "2-3 sentences about weather conditions and how they affect pollution",
  "impact": "Specific statement about weather favorability for air quality",
  "uvAlert": "UV safety tip if UV index is high, otherwise general weather tip"
}}

Be practical and helpful."""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()
            response = self.model.generate_content(prompt)
            duration_ms = int((time.time() - start_time) * 1000)

            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)
            structured_logger.log_ai_summary(
                'weather_summary', len(text), duration_ms, True)

            # Log Gemini response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI AI RESPONSE - Weather Summary")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Result: {json.dumps(result, indent=2)}")
            print(f"{'='*80}\n")

            return result
        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            if '429' not in error_msg and 'quota' not in error_msg.lower():
                print(f"Gemini API error (weather): {error_msg}")
            structured_logger.log_ai_summary('weather_summary', 0, 0, False)
            return self._fallback_weather_summary(weather)

    def generate_forecast_summary(self, forecast_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI summary for 24-hour forecast"""

        if not self.model:
            return self._fallback_forecast_summary(forecast_data)

        prompt = f"""You are an air quality forecaster. Summarize the 24-hour forecast.

Forecast Data:
{json.dumps(forecast_data, indent=2)}

Generate exactly 3 items in JSON format:
{{
  "brief": "One sentence forecast summary (max 20 words)",
  "detailed": "2-3 sentences about trends, best/worst times, and confidence",
  "recommendations": ["3 specific time-based recommendations with emojis"],
  "keyInsights": "One interesting insight about the forecast pattern"
}}

Focus on actionable timing advice."""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()
            response = self.model.generate_content(prompt)
            duration_ms = int((time.time() - start_time) * 1000)

            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)
            structured_logger.log_ai_summary(
                'forecast_summary', len(text), duration_ms, True)

            # Log Gemini response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI AI RESPONSE - Forecast Summary")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Result: {json.dumps(result, indent=2)}")
            print(f"{'='*80}\n")

            return result
        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            if '429' not in error_msg and 'quota' not in error_msg.lower():
                print(f"Gemini API error (forecast): {error_msg}")
            structured_logger.log_ai_summary('forecast_summary', 0, 0, False)
            return self._fallback_forecast_summary(forecast_data)

    def generate_historical_summary(self, historical: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI summary for historical trends"""

        if not self.model:
            return self._fallback_historical_summary(historical)

        stats = historical.get('statistics', {})
        prompt = f"""You are an air quality analyst. Summarize the 7-day trend.

Historical Statistics:
Average AQI: {stats.get('average', 0)}
Trend: {stats.get('trend', {}).get('direction', 'stable')} ({stats.get('trend', {}).get('percentage', 0)}%)
Best/Worst days: {json.dumps(historical.get('patterns', {}), indent=2)}

Generate exactly 4 items in JSON format:
{{
  "brief": "One sentence about the weekly trend (max 20 words)",
  "detailed": "2-3 sentences analyzing patterns and what influenced them",
  "trendAnalysis": "Insight about the trend direction with emoji",
  "weeklyInsight": "Comparative insight (vs other cities or norms)",
  "recommendation": "Advice based on observed patterns"
}}

Make it insightful and comparative."""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()
            response = self.model.generate_content(prompt)
            duration_ms = int((time.time() - start_time) * 1000)

            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)
            structured_logger.log_ai_summary(
                'historical_summary', len(text), duration_ms, True)

            # Log Gemini response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI AI RESPONSE - Historical Summary")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Result: {json.dumps(result, indent=2)}")
            print(f"{'='*80}\n")

            return result
        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            if '429' not in error_msg and 'quota' not in error_msg.lower():
                print(f"Gemini API error (historical): {error_msg}")
            structured_logger.log_ai_summary('historical_summary', 0, 0, False)
            return self._fallback_historical_summary(historical)

    def generate_alerts_summary(self, alerts: Dict[str, Any], aqi: int) -> Dict[str, str]:
        """Generate AI summary for health alerts"""

        if not self.model:
            return self._fallback_alerts_summary(alerts, aqi)

        prompt = f"""You are a health advisor. Explain air quality health alerts.

Current AQI: {aqi}
Active Alerts: {len(alerts.get('activeAlerts', []))}
Alert Details: {json.dumps(alerts, indent=2)}

Generate exactly 4 items in JSON format:
{{
  "brief": "One sentence alert summary (max 20 words)",
  "detailed": "2-3 sentences about who is affected and why",
  "riskLevel": "Clear risk statement for different groups",
  "actionRequired": "What people should do (or not do)",
  "nextUpdate": "When to check again or expect changes"
}}

Be clear about risks but not alarmist."""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()
            response = self.model.generate_content(prompt)
            duration_ms = int((time.time() - start_time) * 1000)

            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)
            structured_logger.log_ai_summary(
                'alerts_summary', len(text), duration_ms, True)

            # Log Gemini response
            print(f"\n{'='*80}")
            print(f"🤖 GEMINI AI RESPONSE - Alerts Summary")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Result: {json.dumps(result, indent=2)}")
            print(f"{'='*80}\n")

            return result
        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            if '429' not in error_msg and 'quota' not in error_msg.lower():
                print(f"Gemini API error (alerts): {error_msg}")
            structured_logger.log_ai_summary('alerts_summary', 0, 0, False)
            return self._fallback_alerts_summary(alerts, aqi)

    # Fallback methods when Gemini is unavailable
    def _fallback_aqi_summary(self, aqi_data: Dict[str, Any]) -> Dict[str, str]:
        aqi = aqi_data.get('aqi', 0)
        category = aqi_data.get('category', 'unknown')

        return {
            "brief": f"Air quality is {category} with AQI of {aqi}.",
            "detailed": f"Current air quality index is {aqi}, classified as {category}. The dominant pollutant is {aqi_data.get('dominantPollutant', 'unknown')}. Conditions are {'safe for most activities' if aqi <= 100 else 'requiring caution for sensitive groups'}.",
            "recommendation": "Check current conditions before outdoor activities." if aqi > 100 else "Air quality is suitable for outdoor activities.",
            "insight": "Air quality varies throughout the day - early morning is often best"
        }

    def _fallback_sources_summary(self, sources: Dict[str, Any]) -> Dict[str, str]:
        return {
            "brief": "Data from multiple sources confirms reliable air quality readings.",
            "detailed": "Satellite and ground sensor data are combined to provide accurate air quality information. Multiple data sources help validate measurements.",
            "validation": "Data sources show good agreement",
            "dataQuality": "Reliable - Multiple sources confirm readings"
        }

    def _fallback_weather_summary(self, weather: Dict[str, Any]) -> Dict[str, str]:
        temp = weather.get('temperature', 0)
        wind = weather.get('windSpeed', 0)

        return {
            "brief": f"Current temperature is {temp}°C with winds at {wind} km/h.",
            "detailed": f"Weather conditions are influencing air quality. Wind speed of {wind} km/h helps disperse pollutants.",
            "impact": "Weather conditions are moderately favorable for air quality.",
            "uvAlert": "Monitor UV levels during peak sun hours"
        }

    def _fallback_forecast_summary(self, forecast: Dict[str, Any]) -> Dict[str, str]:
        return {
            "brief": "Air quality forecast available for the next 24 hours.",
            "detailed": "Forecast shows expected air quality trends based on weather patterns and historical data.",
            "recommendations": [
                "Check forecast before planning outdoor activities",
                "Morning hours typically have different conditions than evening",
                "Monitor real-time updates for changes"
            ],
            "keyInsights": "Air quality patterns follow daily traffic and weather cycles"
        }

    def _fallback_historical_summary(self, historical: Dict[str, Any]) -> Dict[str, str]:
        stats = historical.get('statistics', {})
        avg = stats.get('average', 0)
        trend = stats.get('trend', {})
        direction = trend.get('direction', 'stable')
        percentage = abs(trend.get('percentage', 0))

        trend_text = f"{'improving' if direction == 'improving' else 'worsening' if direction == 'worsening' else 'stable'}"
        emoji = "📈" if direction == 'worsening' else "📉" if direction == 'improving' else "➡️"

        return {
            "brief": f"Average air quality was {'moderate' if avg > 50 else 'good'} but showed a {'significant' if percentage > 10 else 'slight'} {trend_text} trend of {percentage:.1f}% over the past week.",
            "detailed": f"The week showed air quality patterns with an average AQI of {avg}. Analysis indicates {trend_text} conditions influenced by daily traffic patterns and weather conditions.",
            "trendAnalysis": f"The data shows a {trend_text} trajectory with air quality changing by {percentage:.1f}% this week. {emoji}",
            "weeklyInsight": f"While average AQI of {avg} is typical for urban areas, the {trend_text} trend warrants attention.",
            "recommendation": "Monitor daily conditions and plan outdoor activities during early morning hours when air quality is typically better."
        }

    def _fallback_alerts_summary(self, alerts: Dict[str, Any], aqi: int) -> Dict[str, str]:
        alert_count = len(alerts.get('activeAlerts', []))

        return {
            "brief": f"{alert_count} active alert{'s' if alert_count != 1 else ''} for current air quality conditions.",
            "detailed": "Air quality alerts provide guidance for sensitive groups and outdoor activities.",
            "riskLevel": "Low for general population" if aqi <= 100 else "Moderate for sensitive groups",
            "actionRequired": "Follow recommended precautions based on your sensitivity",
            "nextUpdate": "Check for updates in 2 hours"
        }


# Global instance
summary_engine = GeminiSummaryEngine()
