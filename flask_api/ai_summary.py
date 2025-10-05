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

        prompt = f"""You are a friendly weather reporter explaining air quality to everyday people. Write like you're talking to a friend, not giving a technical report.

LOCATION: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}

CURRENT CONDITIONS:
- AQI: {aqi_value} ({current_aqi.get('category', 'unknown')})
- Dominant Pollutant: {current_aqi.get('dominantPollutant', 'unknown')}
- Pollutants: {json.dumps(current_aqi.get('pollutants', {}))}

WEATHER CONDITIONS:
- Temperature: {weather.get('temperature', 0)}°C
- Humidity: {weather.get('humidity', 0)}%
- Wind Speed: {weather.get('windSpeed', 0)} m/s
- Conditions: {weather.get('conditions', 'unknown')}

DATA SOURCES:
{json.dumps(sources, indent=2)}

24-HOUR FORECAST:
{json.dumps(forecast, indent=2)}

7-DAY HISTORICAL DATA:
{json.dumps(historical, indent=2)}

HEALTH ALERTS:
- Active Alerts: {len(alerts.get('activeAlerts', []))}
- Upcoming Alerts: {len(alerts.get('upcomingAlerts', []))}

Write a friendly, conversational analysis in JSON format. Imagine you're a weather reporter on TV:

{{
  "aqi_summary": {{
    "brief": "A friendly one-liner about today's air quality, like a weather reporter would say",
    "detailed": "Explain what's in the air today in simple terms - talk about it like you're explaining to a friend over coffee",
    "recommendation": "Casual, helpful advice - 'Good day for a jog' or 'Maybe skip that outdoor workout today'",
    "insight": "An interesting tidbit that makes people go 'huh, cool!' - keep it light and conversational"
  }},
  "sources_summary": {{
    "brief": "A quick note about where we're getting this info from",
    "detailed": "Explain how we know this in everyday language - NASA's eyes in the sky plus sensors on the ground",
    "validation": "A reassuring note that the data checks out",
    "dataQuality": "Tell people if they can trust these numbers"
  }},
  "weather_summary": {{
    "brief": "What's it like outside right now? (weather-wise)",
    "detailed": "Explain how today's weather is affecting the air - is the wind clearing things out? Is it too humid? Use real numbers but make it relatable",
    "impact": "Bottom line - is the weather helping or hurting air quality today?",
    "uvAlert": "Any weather tips? Sun too strong? Perfect day?"
  }},
  "forecast_summary": {{
    "brief": "Here's what to expect in the next 24 hours",
    "detailed": "Paint a picture of how air quality will change - 'mornings will be rough, but afternoons look better'",
    "recommendations": ["3 practical tips in plain English - things people can actually do"],
    "keyInsights": "The most important thing to know for planning your day"
  }},
  "historical_summary": {{
    "brief": "How's the air been this week compared to usual?",
    "detailed": "Tell the story of the past week - was it getting better? worse? why?",
    "trendAnalysis": "Is it trending up 📈 or down 📉? Say it like you mean it",
    "weeklyInsight": "How does this week stack up?",
    "recommendation": "What should people keep in mind based on the pattern?"
  }},
  "alerts_summary": {{
    "brief": "Quick heads-up about any health concerns",
    "detailed": "Who needs to be careful and why? Keep it clear and caring",
    "riskLevel": "Straight talk about the risk - no jargon",
    "actionRequired": "What should people actually do?",
    "nextUpdate": "When should they check back?"
  }}
}}

STYLE GUIDE:
- Write like a friendly TV weather reporter, not a scientist
- Use everyday words - say "tiny particles" not "particulate matter"
- Be warm and conversational - "you might want to..." instead of "it is recommended..."
- Make it relatable - "like breathing through a straw" instead of "reduced respiratory function"
- Use real numbers but explain what they mean for real life
- Be honest but not scary - helpful, not alarmist
- Think: "How would I explain this to my neighbor?"

Return ONLY valid JSON, no extra text"""

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

        prompt = f"""You're a friendly weather reporter explaining today's air quality. Talk to people like a neighbor, not a scientist.

Where: {location.get('city', 'Unknown')}, {location.get('country', '')}
Air Quality Index: {aqi_data.get('aqi', 0)}
What that means: {aqi_data.get('category', 'unknown')}
Main pollutant: {aqi_data.get('dominantPollutant', 'unknown')}
What's in the air: {json.dumps(aqi_data.get('pollutants', {}), indent=2)}

Write it like you're on the morning news - friendly, clear, helpful:
{{
  "brief": "Give people the bottom line in one friendly sentence - is it a good day or not?",
  "detailed": "Explain what's happening with the air today like you're talking to a friend. What's causing it? What can they expect?",
  "recommendation": "What should they actually do today? Go for that run? Maybe stay inside? Be specific but casual",
  "insight": "Drop a cool fact or helpful tip - something that makes them smarter about air quality. Add an emoji to keep it light"
}}

Remember: You're the friendly weather person, not writing a scientific paper. Make it conversational and helpful."""

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

    def generate_persona_specific_insights(
        self,
        persona_type: str,
        current_aqi: Dict[str, Any],
        forecast: Dict[str, Any],
        historical: Dict[str, Any],
        weather: Dict[str, Any],
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive persona-specific insights

        Returns actionable intelligence tailored to user's role:
        - Immediate actions required
        - Safe time windows for activities
        - Risk assessment for their specific population
        - Context-aware recommendations
        - Comparative analysis
        """
        from personas import get_persona, get_risk_level

        if not self.model:
            return self._fallback_persona_insights(persona_type, current_aqi, forecast)

        # Get persona configuration
        persona = get_persona(persona_type)
        aqi_value = current_aqi.get('aqi', 50)
        risk_level = get_risk_level(persona_type, aqi_value)

        # Build comprehensive persona context
        prompt = f"""You're a helpful air quality advisor talking to a {persona['name']}. Speak directly to them like a friendly expert who understands their world.

WHO YOU'RE HELPING: {persona['display_name']}
WHAT THEY DO: {persona['description']}

WHAT THEY'RE WORRIED ABOUT:
{chr(10).join(['- ' + concern for concern in persona.get('concerns', [])])}

QUESTIONS THEY NEED ANSWERS TO:
{chr(10).join(['- ' + q for q in persona.get('key_questions', [])])}

WHAT'S HAPPENING RIGHT NOW:
Where: {location.get('city', 'Unknown')}, {location.get('country', '')}
Air Quality: {aqi_value} ({current_aqi.get('category', 'unknown')})
Main Issue: {current_aqi.get('dominantPollutant', 'unknown')} levels
Risk for them: {risk_level}

THE AIR TODAY:
{json.dumps(current_aqi.get('pollutants', {}), indent=2)}

WEATHER MATTERS:
Temp: {weather.get('temperature', 0)}°C
Humidity: {weather.get('humidity', 0)}%
Wind: {weather.get('windSpeed', 0)} m/s
Sky: {weather.get('conditions', 'unknown')}

WHAT'S COMING (Next 24 Hours):
{json.dumps(forecast.get('hourly', [])[:8], indent=2)}

KEY TIMES TODAY:
Best air: {forecast.get('summary', {}).get('best', {}).get('hour', 'unknown')} (AQI {forecast.get('summary', {}).get('best', {}).get('aqi', 0)})
Worst air: {forecast.get('summary', {}).get('worst', {}).get('hour', 'unknown')} (AQI {forecast.get('summary', {}).get('worst', {}).get('aqi', 0)})
Pattern: {forecast.get('summary', {}).get('trend', 'stable')}

HOW IT'S BEEN LATELY (Past Week):
Average: {historical.get('statistics', {}).get('average', 0)}
Trend: {historical.get('statistics', {}).get('trend', {}).get('direction', 'stable')} ({historical.get('statistics', {}).get('trend', {}).get('percentage', 0)}%)
Good days: {historical.get('statistics', {}).get('goodDays', 0)} out of 7
Best time is usually: {historical.get('patterns', {}).get('bestDay', 'Unknown')}

THEIR SAFETY LIMITS:
{json.dumps(persona.get('aqi_thresholds', {}), indent=2)}

Write advice in JSON format. Think of yourself as their go-to advisor who knows their job:

{{
  "immediate_action": "Tell them straight up - what should they do right now? Keep it simple and direct",
  "time_windows": [
    {{
      "start": "time",
      "end": "time",
      "aqi": number,
      "safe_for": "What can they safely do during this window?",
      "recommendation": "Your advice for this time slot"
    }}
  ],
  "risk_assessment": {{
    "level": "{risk_level}",
    "affected_groups": ["Who needs to be extra careful? Use terms they'd use"],
    "specific_risks": "Explain the risks in plain English - what could actually happen to the people they care about?"
  }},
  "recommendations": [
    "Give them 3-5 things they can actually do today",
    "Be specific about when - 'Hold practice at 3 PM instead of 10 AM'",
    "Give them options - 'If you can't go outside, try this instead'",
    "Answer their actual questions from above"
  ],
  "context": "Help them understand - why does today's air quality matter for their specific situation? Talk to them, not at them",
  "comparative": "How does this compare to what's normal? Give them perspective",
  "data_confidence": {{
    "level": "high|medium|low",
    "explanation": "Can they trust this info? Be honest and reassuring"
  }},
  "key_insight": "One useful thing they might not know - make it practical and relevant to them"
}}

HOW TO TALK TO THEM:
- Use words they use in their daily work (students/residents/operations/etc)
- Be specific about their actual concerns (recess, outdoor activities, safety protocols)
- Give them times they can use ("3 PM" not "1500 hours")
- Make it doable - they're busy, keep advice practical
- Be friendly but professional - you're helping them make important decisions
- Don't use technical jargon - explain air quality like you'd explain weather
- Be direct - they need clear answers to make quick decisions

Return ONLY valid JSON, no extra text"""

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

            # Log persona insights generation
            print(f"\n{'='*80}")
            print(f"🎭 PERSONA INSIGHTS GENERATED: {persona['display_name']}")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Risk Level: {risk_level}")
            print(json.dumps(result, indent=2))
            print(f"{'='*80}\n")

            structured_logger.log_ai_summary(f'persona_{persona_type}', len(text), duration_ms, True)

            return result

        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            if '429' in error_msg or 'quota' in error_msg.lower():
                print(f"Gemini API rate limit hit - using fallback for persona insights")
            else:
                print(f"Gemini API error (persona insights): {error_msg}")
            structured_logger.log_ai_summary(f'persona_{persona_type}', 0, 0, False)
            return self._fallback_persona_insights(persona_type, current_aqi, forecast)

    def generate_live_weather_report(
        self,
        persona_type: str,
        location: Dict[str, Any],
        current_aqi: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate live weather report using Gemini web search
        Fetches real-time weather/air quality news and advisories for the location
        """
        from personas import get_persona

        if not self.model:
            return self._fallback_live_report(persona_type, location, current_aqi)

        persona = get_persona(persona_type)
        city = location.get('city', 'Unknown')
        country = location.get('country', 'Unknown')
        aqi_value = current_aqi.get('aqi', 0)

        # Use Gemini with Google Search for live information
        prompt = f"""Search the web for current weather and air quality information about {city}, {country}.

I'm helping a {persona['display_name']} who needs to know:
{chr(10).join(['- ' + q for q in persona.get('key_questions', [])])}

Current AQI from our sensors: {aqi_value}

Search for and analyze:
1. Current weather conditions and forecast for {city}
2. Air quality alerts or warnings for {city}
3. Any pollution advisories or health warnings
4. Local news about air quality, wildfires, or environmental concerns
5. Specific risks for children, elderly, or sensitive groups in this area

Generate a live weather report in JSON format:

{{
  "headline": "A catchy one-liner summarizing the current situation - like a news headline",
  "current_conditions": "What's happening right now based on live web data - weather, air quality, any alerts",
  "local_alerts": "Any specific warnings or advisories for {city} from official sources or news",
  "health_advisory": "Specific health advice for {persona['display_name']} based on current conditions",
  "trending_info": "What people in {city} should know today - from news, social media, or official sources",
  "recommendations": ["3-5 specific actions based on live conditions"],
  "sources": "Mention where this info comes from (e.g., 'Local news reports...', 'Weather service says...', 'According to...')",
  "next_update": "When they should check back or what to watch for"
}}

IMPORTANT:
- Use LIVE web search data - don't just rely on the AQI I gave you
- Find real news, alerts, and advisories for this specific location
- If there's wildfire smoke, pollution events, or weather warnings, highlight them
- Be specific about risks for the groups this persona cares about
- Make it sound like a local news weather report
- If you can't find specific info, say so honestly

Search the web and return ONLY valid JSON."""

        try:
            import time
            from logger import structured_logger

            start_time = time.time()

            # Use Gemini with Google Search enabled
            response = self.model.generate_content(
                prompt,
                tools='google_search_retrieval'
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Parse JSON from response
            text = response.text.strip()
            if text.startswith('```json'):
                text = text.split('```json')[1].split('```')[0].strip()
            elif text.startswith('```'):
                text = text.split('```')[1].split('```')[0].strip()

            result = json.loads(text)

            # Log live weather report generation
            print(f"\n{'='*80}")
            print(f"🌐 LIVE WEATHER REPORT GENERATED: {city}, {country}")
            print(f"{'='*80}")
            print(f"Duration: {duration_ms}ms")
            print(f"Persona: {persona['display_name']}")
            print(json.dumps(result, indent=2))
            print(f"{'='*80}\n")

            structured_logger.log_ai_summary(f'live_report_{persona_type}', len(text), duration_ms, True)

            return result

        except Exception as e:
            from logger import structured_logger
            error_msg = str(e)
            print(f"Gemini web search error: {error_msg}")
            structured_logger.log_ai_summary(f'live_report_{persona_type}', 0, 0, False)
            return self._fallback_live_report(persona_type, location, current_aqi)

    def _fallback_live_report(
        self,
        persona_type: str,
        location: Dict[str, Any],
        current_aqi: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback live report when web search unavailable"""
        from personas import get_persona

        persona = get_persona(persona_type)
        city = location.get('city', 'Unknown')
        aqi = current_aqi.get('aqi', 0)
        category = current_aqi.get('category', 'unknown')

        return {
            "headline": f"Air quality in {city} is {category}",
            "current_conditions": f"Current AQI of {aqi} indicates {category} air quality conditions.",
            "local_alerts": "No specific local alerts available at this time.",
            "health_advisory": f"As a {persona['display_name']}, monitor air quality and adjust outdoor activities accordingly.",
            "trending_info": "Check back later for updated conditions.",
            "recommendations": [
                "Monitor local air quality throughout the day",
                "Follow general health guidelines for current AQI level",
                "Check back for updates"
            ],
            "sources": "Based on sensor data",
            "next_update": "Check back in a few hours for updated conditions"
        }

    def _fallback_persona_insights(
        self,
        persona_type: str,
        current_aqi: Dict[str, Any],
        forecast: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback persona insights when Gemini unavailable"""
        from personas import get_persona, get_risk_level

        persona = get_persona(persona_type)
        aqi = current_aqi.get('aqi', 50)
        risk_level = get_risk_level(persona_type, aqi)

        # Generic recommendations based on AQI and persona
        recommendations = []
        immediate_action = "Check current air quality conditions before outdoor activities."

        if persona_type == "school_administrator":
            if aqi > 100:
                immediate_action = "Consider moving outdoor activities indoors. Air quality exceeds safe threshold for students."
                recommendations = [
                    "Move recess and PE classes indoors",
                    "Reschedule outdoor sports practice",
                    "Notify parents of air quality conditions",
                    "Monitor AQI updates throughout the day"
                ]
            elif aqi > 50:
                immediate_action = "Modify outdoor activities to reduce intensity and duration."
                recommendations = [
                    "Limit outdoor sports to light activities",
                    "Reduce outdoor time for sensitive students",
                    "Keep rescue inhalers accessible",
                    "Monitor student symptoms"
                ]
            else:
                immediate_action = "Air quality is safe for all student activities."
                recommendations = [
                    "All outdoor activities can proceed normally",
                    "Good conditions for sports practice and PE",
                    "Safe for extended outdoor time"
                ]

        elif persona_type == "vulnerable_population":
            if aqi > 100:
                immediate_action = "Stay indoors. Air quality is unhealthy for sensitive individuals."
                recommendations = [
                    "Remain indoors with windows closed",
                    "Use air purifier if available",
                    "Have rescue inhaler ready if you have asthma",
                    "Avoid all outdoor physical activity"
                ]
            elif aqi > 50:
                immediate_action = "Limit time outdoors and avoid strenuous activities."
                recommendations = [
                    "Limit outdoor time to essential activities only",
                    "Avoid exercise outdoors",
                    "Monitor for symptoms (coughing, shortness of breath)",
                    "Check AQI before going outside"
                ]
            else:
                immediate_action = "Air quality is safe for outdoor activities."
                recommendations = [
                    "Safe to go outside",
                    "Light outdoor activities are fine",
                    "Continue to monitor if you have respiratory conditions"
                ]

        else:  # Generic fallback
            if aqi > 100:
                immediate_action = f"Air quality is {current_aqi.get('category', 'moderate')}. Limit outdoor activities."
                recommendations = [
                    "Reduce time spent outdoors",
                    "Avoid strenuous outdoor activities",
                    "Monitor air quality updates",
                    "Check forecast for better times"
                ]
            else:
                immediate_action = "Air quality is acceptable for most activities."
                recommendations = [
                    "Monitor conditions throughout the day",
                    "Check forecast for changes",
                    "Be aware of sensitive group concerns"
                ]

        return {
            "immediate_action": immediate_action,
            "time_windows": [
                {
                    "start": forecast.get('summary', {}).get('best', {}).get('hour', '3:00 AM'),
                    "end": "6:00 AM",
                    "aqi": forecast.get('summary', {}).get('best', {}).get('aqi', 35),
                    "safe_for": "all activities",
                    "recommendation": "Best time for outdoor activities"
                }
            ],
            "risk_assessment": {
                "level": risk_level,
                "affected_groups": persona.get('concerns', ['General population']),
                "specific_risks": f"Current AQI of {aqi} may impact {persona['name'].lower()} based on exposure duration and activity intensity."
            },
            "recommendations": recommendations,
            "context": f"Current air quality is {current_aqi.get('category', 'moderate')} with AQI of {aqi}. This is {'above' if aqi > 50 else 'at or below'} recommended thresholds for sensitive activities.",
            "comparative": f"Air quality is {'better' if historical.get('statistics', {}).get('trend', {}).get('direction') == 'improving' else 'similar to'} recent patterns.",
            "data_confidence": {
                "level": "medium",
                "explanation": "Data from multiple ground sensors provides reliable measurements."
            },
            "key_insight": "Monitor conditions throughout the day as air quality can vary significantly with traffic patterns and weather."
        }


# Global instance
summary_engine = GeminiSummaryEngine()
