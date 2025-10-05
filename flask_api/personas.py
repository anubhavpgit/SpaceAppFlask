"""
Persona Definitions and Configuration
Defines user personas with specific needs, thresholds, and priorities
"""

from typing import Dict, Any, List


# Persona type constants
PERSONA_VULNERABLE = "vulnerable_population"
PERSONA_SCHOOL = "school_administrator"
PERSONA_ELDERCARE = "eldercare_manager"
PERSONA_GOVERNMENT = "government_official"
PERSONA_TRANSPORT = "transportation_authority"
PERSONA_PARKS = "parks_recreation"
PERSONA_EMERGENCY = "emergency_response"
PERSONA_INSURANCE = "insurance_assessor"
PERSONA_CITIZEN = "citizen_scientist"
PERSONA_GENERAL = "general"


PERSONA_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    PERSONA_VULNERABLE: {
        "name": "Vulnerable Individual",
        "display_name": "Parent/Guardian of Vulnerable Person",
        "description": "Elderly, children, individuals with asthma, respiratory or cardiovascular conditions",
        "icon": "shield-alert",
        "sensitivities": ["respiratory", "cardiovascular", "age_sensitive"],
        "aqi_thresholds": {
            "safe": 50,          # Can go outside safely
            "caution": 75,       # Limit time outdoors
            "unsafe": 100,       # Stay indoors
            "emergency": 150     # Seek medical attention if symptoms
        },
        "priority_pollutants": ["pm25", "o3", "no2"],  # Most concerning
        "activity_restrictions": {
            "light_outdoor": 75,      # Walking, light play
            "moderate_outdoor": 50,   # Extended outdoor time
            "strenuous": 40           # Exercise, sports
        },
        "concerns": [
            "Respiratory health impacts",
            "Symptom triggers (wheezing, shortness of breath)",
            "Safe time windows for outdoor activities",
            "When to use rescue inhaler",
            "When to seek medical attention"
        ],
        "key_questions": [
            "Is it safe to go outside?",
            "Should I use my inhaler before going out?",
            "What time of day is safest?",
            "Do I need to keep my child indoors?"
        ]
    },

    PERSONA_SCHOOL: {
        "name": "School Administrator",
        "display_name": "School/Athletic Administrator",
        "description": "Principals, athletic directors, coaches making outdoor activity decisions",
        "icon": "school",
        "sensitivities": ["student_health", "liability", "performance_impact"],
        "aqi_thresholds": {
            "full_activities": 50,      # All outdoor activities OK
            "modified_activities": 100, # Reduce intensity/duration
            "indoor_only": 150,         # Cancel outdoor activities
            "emergency": 200            # School closure consideration
        },
        "priority_pollutants": ["pm25", "o3"],  # Most impact on athletics
        "decision_points": [
            "recess_schedule",
            "outdoor_sports_practice",
            "physical_education",
            "field_trips",
            "outdoor_events"
        ],
        "activity_restrictions": {
            "recess": 100,              # Regular recess
            "pe_class": 75,             # Physical education
            "sports_practice": 50,       # Athletic practice/games
            "extended_outdoor": 75      # Field trips, outdoor events
        },
        "concerns": [
            "Student safety and health",
            "Liability for outdoor activities",
            "Performance impact on student athletes",
            "Communication to parents",
            "Schedule modifications"
        ],
        "key_questions": [
            "Should we cancel outdoor sports practice?",
            "Can students have recess outside?",
            "What time is best for PE class?",
            "Do we need to notify parents?"
        ]
    },

    PERSONA_ELDERCARE: {
        "name": "Eldercare Facility Manager",
        "display_name": "Senior Care Facility Manager",
        "description": "Nursing homes, assisted living, senior centers managing resident health",
        "icon": "heart-pulse",
        "sensitivities": ["senior_health", "facility_management", "respiratory"],
        "aqi_thresholds": {
            "safe": 50,
            "monitor": 75,         # Increase monitoring
            "restrict": 100,       # Keep residents indoors
            "critical": 150        # Enhanced air filtration, medical standby
        },
        "priority_pollutants": ["pm25", "pm10", "o3"],
        "facility_actions": {
            "windows": 75,              # Threshold to close windows
            "air_filtration": 100,      # Activate HEPA filters
            "outdoor_restriction": 100, # No outdoor activities
            "medical_alert": 150        # Alert medical staff
        },
        "concerns": [
            "Respiratory health of seniors",
            "Cardiovascular impact",
            "Facility air quality management",
            "Medical response readiness",
            "Staff communication"
        ],
        "key_questions": [
            "Should we close windows?",
            "Do we need to activate air purifiers?",
            "Can residents go outside?",
            "Should we alert medical staff?",
            "Do we need to stock extra medications?"
        ]
    },

    PERSONA_GOVERNMENT: {
        "name": "Government Official",
        "display_name": "Policy Maker/Municipal Leader",
        "description": "City officials, environmental agencies, public health departments",
        "icon": "landmark",
        "sensitivities": ["population_exposure", "policy_effectiveness", "public_health"],
        "aqi_thresholds": {
            "good": 50,
            "advisory": 100,         # Issue health advisory
            "alert": 150,            # Air quality alert
            "emergency": 200         # Air quality emergency
        },
        "priority_pollutants": ["pm25", "o3", "no2"],
        "focus_areas": [
            "population_weighted_exposure",
            "exceedance_days",
            "trend_analysis",
            "policy_impact_assessment",
            "public_communication"
        ],
        "metrics": [
            "Percentage of population affected",
            "Days exceeding standards",
            "Long-term trends",
            "Effectiveness of clean air initiatives",
            "Comparison to other municipalities"
        ],
        "concerns": [
            "Public health protection",
            "Policy effectiveness",
            "Communication strategy",
            "Resource allocation",
            "Regulatory compliance"
        ],
        "key_questions": [
            "Should we issue a public health advisory?",
            "Are our clean air policies effective?",
            "How do we compare to other cities?",
            "What's the population exposure level?",
            "Should we implement traffic restrictions?"
        ]
    },

    PERSONA_TRANSPORT: {
        "name": "Transportation Authority",
        "display_name": "Transit/Traffic Manager",
        "description": "DOT, port authority, airport operations, traffic management",
        "icon": "train-track",
        "sensitivities": ["visibility", "operations", "emissions"],
        "aqi_thresholds": {
            "normal": 75,
            "advisory": 100,        # Issue travel advisories
            "restrictions": 150,    # Consider restrictions
            "critical": 200         # Emergency protocols
        },
        "priority_pollutants": ["no2", "pm25", "co"],  # Traffic-related
        "operational_concerns": [
            "visibility_impacts",
            "port_operations",
            "airport_operations",
            "traffic_congestion",
            "emissions_hotspots"
        ],
        "metrics": [
            "Visibility levels",
            "Traffic contribution to AQI",
            "Transit ridership impact",
            "Congestion patterns",
            "Alternative route recommendations"
        ],
        "concerns": [
            "Operations safety",
            "Traffic management",
            "Emissions reduction",
            "Public transit promotion",
            "Emergency routing"
        ],
        "key_questions": [
            "Are visibility levels safe for operations?",
            "Should we promote public transit?",
            "Are traffic emissions a major contributor?",
            "Do we need alternative routing?",
            "Should we implement congestion pricing?"
        ]
    },

    PERSONA_PARKS: {
        "name": "Parks & Recreation",
        "display_name": "Parks/Recreation Coordinator",
        "description": "Parks departments, rec centers, event coordinators, trail managers",
        "icon": "trees",
        "sensitivities": ["outdoor_activities", "event_safety", "visitor_experience"],
        "aqi_thresholds": {
            "all_activities": 50,
            "light_activities": 100,   # Walking, casual use OK
            "restricted": 150,         # Post warnings
            "closed": 200              # Close trails/facilities
        },
        "priority_pollutants": ["pm25", "o3"],
        "activity_levels": {
            "light": 100,          # Walking, picnicking
            "moderate": 75,        # Hiking, biking
            "strenuous": 50,       # Running, intense sports
            "events": 75           # Organized events
        },
        "concerns": [
            "Visitor safety",
            "Event scheduling",
            "Warning signage",
            "Liability",
            "User experience"
        ],
        "key_questions": [
            "Should we cancel outdoor events?",
            "Do we need to post warnings on trails?",
            "What activities are safe?",
            "Should we close certain areas?",
            "How do we communicate with visitors?"
        ]
    },

    PERSONA_EMERGENCY: {
        "name": "Emergency Response",
        "display_name": "Emergency Management",
        "description": "Fire departments, disaster response, wildfire management, crisis teams",
        "icon": "shield-check",
        "sensitivities": ["rapid_deterioration", "population_risk", "resource_deployment"],
        "aqi_thresholds": {
            "normal": 100,
            "elevated": 150,        # Increase monitoring
            "alert": 200,           # Prepare response
            "emergency": 300        # Active response
        },
        "priority_pollutants": ["pm25", "pm10", "co"],  # Wildfire indicators
        "response_triggers": {
            "monitoring": 150,
            "pre_positioning": 200,
            "evacuation_prep": 250,
            "active_evacuation": 300
        },
        "concerns": [
            "Rapid air quality deterioration",
            "Population exposure",
            "Evacuation readiness",
            "Resource allocation",
            "Communication protocols"
        ],
        "key_questions": [
            "Is air quality deteriorating rapidly?",
            "Should we prepare for evacuations?",
            "What's the population at risk?",
            "Do we need to pre-position resources?",
            "Are wildfires a contributing factor?"
        ]
    },

    PERSONA_INSURANCE: {
        "name": "Insurance Risk Assessor",
        "display_name": "Insurance/Risk Analyst",
        "description": "Insurance companies, risk assessors evaluating health and property implications",
        "icon": "file-chart-column",
        "sensitivities": ["long_term_trends", "health_correlation", "regional_risk"],
        "aqi_thresholds": {
            "low_risk": 50,
            "moderate_risk": 100,
            "elevated_risk": 150,
            "high_risk": 200
        },
        "priority_pollutants": ["pm25", "o3", "no2"],
        "analysis_focus": [
            "long_term_exposure_trends",
            "health_event_correlation",
            "regional_risk_assessment",
            "seasonal_patterns",
            "policy_risk_scoring"
        ],
        "metrics": [
            "Days exceeding thresholds",
            "Annual average AQI",
            "Trend direction",
            "Comparison to regional norms",
            "Health claims correlation"
        ],
        "concerns": [
            "Long-term exposure patterns",
            "Health outcome correlation",
            "Regional risk assessment",
            "Premium adjustments",
            "Claims forecasting"
        ],
        "key_questions": [
            "What are long-term exposure trends?",
            "How does this correlate with health claims?",
            "What's the regional risk profile?",
            "Are conditions improving or worsening?",
            "How does this area compare to others?"
        ]
    },

    PERSONA_CITIZEN: {
        "name": "Citizen Scientist",
        "display_name": "Citizen Scientist/Data Contributor",
        "description": "Community members contributing to air quality monitoring and data collection",
        "icon": "microscope",
        "sensitivities": ["data_quality", "contribution_impact", "data_gaps"],
        "aqi_thresholds": {
            "normal": 100,
            "elevated": 150,
            "high": 200,
            "critical": 300
        },
        "priority_pollutants": ["pm25", "pm10", "o3", "no2"],  # All pollutants
        "focus_areas": [
            "data_quality_assessment",
            "measurement_gaps",
            "sensor_validation",
            "community_impact",
            "data_contribution"
        ],
        "concerns": [
            "Data accuracy and validation",
            "Coverage gaps",
            "Measurement priorities",
            "Community benefit",
            "Scientific contribution"
        ],
        "key_questions": [
            "Where are the data gaps?",
            "How accurate are ground sensors?",
            "What measurements are priorities?",
            "How does satellite data compare to ground truth?",
            "Where should we deploy more sensors?"
        ]
    },

    PERSONA_GENERAL: {
        "name": "General User",
        "display_name": "General Public",
        "description": "General population without specific role",
        "icon": "user",
        "sensitivities": ["general_health", "outdoor_activities"],
        "aqi_thresholds": {
            "good": 50,
            "moderate": 100,
            "unhealthy_sensitive": 150,
            "unhealthy": 200
        },
        "priority_pollutants": ["pm25", "o3"],
        "concerns": [
            "Is it safe to be outdoors?",
            "Air quality trends",
            "When conditions will improve"
        ],
        "key_questions": [
            "What's the current air quality?",
            "Is it safe to exercise outside?",
            "When will conditions improve?",
            "What are the main pollutants?"
        ]
    }
}


def get_persona(persona_type: str) -> Dict[str, Any]:
    """Get persona definition by type"""
    return PERSONA_DEFINITIONS.get(persona_type, PERSONA_DEFINITIONS[PERSONA_GENERAL])


def get_all_personas() -> List[Dict[str, Any]]:
    """Get all persona definitions with type keys"""
    return [
        {"type": key, **value}
        for key, value in PERSONA_DEFINITIONS.items()
        if key != PERSONA_GENERAL  # Exclude general from list
    ]


def get_persona_threshold(persona_type: str, threshold_name: str) -> int:
    """Get specific threshold value for persona"""
    persona = get_persona(persona_type)
    return persona.get("aqi_thresholds", {}).get(threshold_name, 100)


def get_risk_level(persona_type: str, aqi: int) -> str:
    """
    Determine risk level for persona based on AQI
    Returns: 'low', 'moderate', 'high', 'critical'
    """
    persona = get_persona(persona_type)
    thresholds = persona.get("aqi_thresholds", {})

    # Get threshold values (with fallbacks)
    if "safe" in thresholds and aqi <= thresholds["safe"]:
        return "low"
    elif "caution" in thresholds and aqi <= thresholds["caution"]:
        return "moderate"
    elif "unsafe" in thresholds and aqi <= thresholds["unsafe"]:
        return "high"
    else:
        return "critical"


def is_activity_safe(persona_type: str, activity_type: str, aqi: int) -> bool:
    """Check if specific activity is safe for persona at given AQI"""
    persona = get_persona(persona_type)

    # Check activity_restrictions
    if "activity_restrictions" in persona:
        threshold = persona["activity_restrictions"].get(activity_type)
        if threshold:
            return aqi <= threshold

    # Fallback to general thresholds
    thresholds = persona.get("aqi_thresholds", {})
    safe_threshold = thresholds.get("safe", thresholds.get("full_activities", 50))
    return aqi <= safe_threshold
