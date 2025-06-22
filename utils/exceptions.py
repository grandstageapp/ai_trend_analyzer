"""
Comprehensive exception hierarchy for AI Trends Analyzer
"""
import uuid
from typing import Optional

class AITrendsException(Exception):
    """Base exception for AI Trends Analyzer"""
    
    def __init__(self, message: str, correlation_id: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]
        self.cause = cause
        self.message = message
    
    def __str__(self):
        return f"[{self.correlation_id}] {self.message}"

# API Related Exceptions
class APIException(AITrendsException):
    """Base class for API-related exceptions"""
    pass

class TwitterAPIException(APIException):
    """Twitter/X API specific exceptions"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code

class OpenAIAPIException(APIException):
    """OpenAI API specific exceptions"""
    
    def __init__(self, message: str, error_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.error_type = error_type

class RateLimitException(APIException):
    """Rate limit exceeded exception"""
    
    def __init__(self, message: str, reset_time: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.reset_time = reset_time

# Database Related Exceptions
class DatabaseException(AITrendsException):
    """Base class for database-related exceptions"""
    pass

class DataIntegrityException(DatabaseException):
    """Data integrity violation"""
    pass

class ConnectionException(DatabaseException):
    """Database connection issues"""
    pass

# Processing Related Exceptions
class ProcessingException(AITrendsException):
    """Base class for data processing exceptions"""
    pass

class TrendAnalysisException(ProcessingException):
    """Trend analysis specific exceptions"""
    pass

class EmbeddingException(ProcessingException):
    """Embedding generation exceptions"""
    pass

# Configuration Related Exceptions
class ConfigurationException(AITrendsException):
    """Configuration-related exceptions"""
    pass

class ValidationException(AITrendsException):
    """Data validation exceptions"""
    pass