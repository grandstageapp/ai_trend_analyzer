"""
Service manager implementing singleton pattern for service instances
"""
import logging
from typing import Optional
from threading import Lock
from services.twitter_service import TwitterService
from services.trend_service import TrendService
from services.openai_service import OpenAIService
from config import Config

logger = logging.getLogger(__name__)

class ServiceManager:
    """Singleton service manager to prevent multiple service instantiation"""
    
    _instance: Optional['ServiceManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._twitter_service: Optional[TwitterService] = None
            self._trend_service: Optional[TrendService] = None
            self._openai_service: Optional[OpenAIService] = None
            self._config: Optional[Config] = None
            self._initialized = True
            logger.info("ServiceManager initialized")
    
    @property
    def twitter_service(self) -> TwitterService:
        """Get or create Twitter service instance"""
        if self._twitter_service is None:
            self._twitter_service = TwitterService()
            logger.debug("Created new TwitterService instance")
        return self._twitter_service
    
    @property
    def trend_service(self) -> TrendService:
        """Get or create Trend service instance"""
        if self._trend_service is None:
            self._trend_service = TrendService()
            logger.debug("Created new TrendService instance")
        return self._trend_service
    
    @property
    def openai_service(self) -> OpenAIService:
        """Get or create OpenAI service instance"""
        if self._openai_service is None:
            self._openai_service = OpenAIService()
            logger.debug("Created new OpenAIService instance")
        return self._openai_service
    
    @property
    def config(self) -> Config:
        """Get or create Config instance"""
        if self._config is None:
            self._config = Config()
            logger.debug("Created new Config instance")
        return self._config
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up ServiceManager resources")
        self._twitter_service = None
        self._trend_service = None
        self._openai_service = None
        self._config = None