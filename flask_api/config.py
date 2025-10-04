"""
ClearSkies API Configuration
"""

import os


class Config:
    """Base configuration"""

    # API Metadata
    API_TITLE = "ClearSkies API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "Unified air quality intelligence platform"

    # Server Configuration
    HOST = "0.0.0.0"
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Response Format
    JSON_SORT_KEYS = False

    # Cache Configuration
    CACHE_TTL_SECONDS = 900  # 15 minutes

    # Rate Limiting
    RATE_LIMIT_PER_HOUR = 100


class DevelopmentConfig(Config):
    """Development environment settings"""
    DEBUG = True
    CACHE_TTL_SECONDS = 300  # 5 minutes


class ProductionConfig(Config):
    """Production environment settings"""
    DEBUG = False
    CACHE_TTL_SECONDS = 900  # 15 minutes


# Export active configuration
config = DevelopmentConfig() if os.getenv(
    'FLASK_ENV') == 'development' else ProductionConfig()
