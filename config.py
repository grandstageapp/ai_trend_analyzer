import os
from datetime import timedelta


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SESSION_SECRET',
                                'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'postgresql://localhost/ai_trends')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    X_API_KEY = os.environ.get('X_API_KEY')
    X_API_SECRET = os.environ.get('X_API_SECRET')
    X_ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN')
    X_ACCESS_TOKEN_SECRET = os.environ.get('X_ACCESS_TOKEN_SECRET')
    X_BEARER_TOKEN = os.environ.get('X_BEARER_TOKEN')

    # Search configuration
    AI_SEARCH_TERMS = ["AI", "artificial intelligence", "generative AI"]

    # Trend scoring weights
    TREND_SCORE_WEIGHTS = {
        'like_weight': 1.0,
        'comment_weight': 1.1,
        'repost_weight': 1.2
    }

    # Background task intervals
    FETCH_POSTS_INTERVAL = timedelta(hours=24)
    CALCULATE_TRENDS_INTERVAL = timedelta(hours=24)

    # Data limits
    MAX_POSTS_PER_DAY = 10
    DEFAULT_SEARCH_RESULTS = 10  # API minimum is 10
    MAX_SEARCH_RESULTS = 10  # API maximum is 100
    SEARCH_TERMS_LIMIT = 3  # Limit search terms to avoid query length issues
    SEARCH_TERMS_LIMIT = 3  # Limit search terms to avoid query length issues
