"""
Type definitions for improved type safety across the application
"""
from typing import Dict, List, Any, Optional, Union, TypeVar, Protocol
from datetime import datetime
from dataclasses import dataclass

# Generic types
T = TypeVar('T')
PostID = str
TrendID = int
AuthorID = int

# Data structures
@dataclass
class PostData:
    """Structured post data from Twitter API"""
    post_id: PostID
    content: str
    created_at: datetime
    author: 'AuthorData'
    metrics: 'EngagementMetrics'

@dataclass
class AuthorData:
    """Structured author data"""
    username: str
    name: Optional[str]
    follower_count: int
    verified: bool
    profile_url: Optional[str]

@dataclass
class EngagementMetrics:
    """Engagement metrics for posts"""
    like_count: int
    reply_count: int
    retweet_count: int
    quote_count: int = 0

@dataclass
class TrendData:
    """Structured trend data"""
    id: TrendID
    title: str
    description: str
    total_posts: int
    created_at: datetime
    latest_score: float

@dataclass
class CacheKey:
    """Cache key structure"""
    prefix: str
    identifier: str
    version: Optional[str] = None
    
    def to_string(self) -> str:
        parts = [self.prefix, self.identifier]
        if self.version:
            parts.append(self.version)
        return ":".join(parts)

# Protocol definitions for dependency injection
class CacheProvider(Protocol):
    """Protocol for cache providers"""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        ...
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache"""
        ...
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        ...

class EmbeddingProvider(Protocol):
    """Protocol for embedding providers"""
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        ...

class TrendAnalyzer(Protocol):
    """Protocol for trend analysis"""
    
    def analyze_and_create_trends(self, posts: List[Any]) -> List[Any]:
        """Analyze posts and create trends"""
        ...
    
    def calculate_trend_scores(self) -> None:
        """Calculate trend scores"""
        ...

# API Response types
TwitterSearchResponse = Dict[str, Any]
OpenAIEmbeddingResponse = Dict[str, Any]
TrendAnalysisResult = Dict[str, Any]

# Configuration types
DatabaseConfig = Dict[str, Union[str, int, bool]]
APIConfig = Dict[str, str]
CachingConfig = Dict[str, Union[str, int]]

# Query result types
QueryResult = Dict[str, Any]
PerformanceMetrics = Dict[str, Union[int, float, str]]
CacheStatistics = Dict[str, Union[int, float]]