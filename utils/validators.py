"""
Consolidated data validation functions
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import re
from utils.type_definitions import PostData, AuthorData, EngagementMetrics
from utils.exceptions import ValidationException

class DataValidator:
    """Centralized data validation utilities"""
    
    @staticmethod
    def validate_post_data(post_data: Dict[str, Any]) -> bool:
        """
        Validate post data structure and content
        
        Args:
            post_data: Dictionary containing post information
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationException: If data is invalid with specific error details
        """
        required_fields = ['post_id', 'content', 'created_at', 'author', 'metrics']
        
        # Check required fields
        for field in required_fields:
            if field not in post_data:
                raise ValidationException(f"Missing required field: {field}")
            
            if post_data[field] is None:
                raise ValidationException(f"Field '{field}' cannot be None")
        
        # Validate post_id format (Twitter post IDs are numeric strings)
        if not re.match(r'^\d+$', str(post_data['post_id'])):
            raise ValidationException(f"Invalid post_id format: {post_data['post_id']}")
        
        # Validate content
        content = post_data['content']
        if not isinstance(content, str) or len(content.strip()) == 0:
            raise ValidationException("Content must be a non-empty string")
        
        if len(content) > 10000:  # Reasonable upper limit
            raise ValidationException("Content exceeds maximum length")
        
        # Validate created_at
        if not isinstance(post_data['created_at'], datetime):
            raise ValidationException("created_at must be a datetime object")
        
        # Validate author data
        if not DataValidator.validate_author_data(post_data['author']):
            return False
        
        # Validate metrics
        if not DataValidator.validate_engagement_metrics(post_data['metrics']):
            return False
        
        return True
    
    @staticmethod
    def validate_author_data(author_data: Dict[str, Any]) -> bool:
        """
        Validate author data structure
        
        Args:
            author_data: Dictionary containing author information
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['username']
        
        for field in required_fields:
            if field not in author_data or not author_data[field]:
                raise ValidationException(f"Missing required author field: {field}")
        
        # Validate username format
        username = author_data['username']
        if not isinstance(username, str):
            raise ValidationException("Username must be a string")
        
        if not re.match(r'^[a-zA-Z0-9_]{1,15}$', username):
            raise ValidationException(f"Invalid username format: {username}")
        
        # Validate follower count if present
        if 'follower_count' in author_data:
            follower_count = author_data['follower_count']
            if not isinstance(follower_count, int) or follower_count < 0:
                raise ValidationException("Follower count must be a non-negative integer")
        
        # Validate verified status if present
        if 'verified' in author_data:
            if not isinstance(author_data['verified'], bool):
                raise ValidationException("Verified status must be a boolean")
        
        return True
    
    @staticmethod
    def validate_engagement_metrics(metrics: Dict[str, Any]) -> bool:
        """
        Validate engagement metrics data
        
        Args:
            metrics: Dictionary containing engagement metrics
            
        Returns:
            True if valid, False otherwise
        """
        required_metrics = ['like_count', 'reply_count', 'retweet_count']
        
        for metric in required_metrics:
            if metric not in metrics:
                raise ValidationException(f"Missing required metric: {metric}")
            
            value = metrics[metric]
            if not isinstance(value, int) or value < 0:
                raise ValidationException(f"Metric '{metric}' must be a non-negative integer")
        
        # Optional metrics
        optional_metrics = ['quote_count', 'impression_count', 'bookmark_count']
        for metric in optional_metrics:
            if metric in metrics:
                value = metrics[metric]
                if not isinstance(value, int) or value < 0:
                    raise ValidationException(f"Optional metric '{metric}' must be a non-negative integer")
        
        return True
    
    @staticmethod
    def validate_trend_data(trend_data: Dict[str, Any]) -> bool:
        """
        Validate trend data structure
        
        Args:
            trend_data: Dictionary containing trend information
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'description']
        
        for field in required_fields:
            if field not in trend_data or not trend_data[field]:
                raise ValidationException(f"Missing required trend field: {field}")
        
        # Validate title
        title = trend_data['title']
        if not isinstance(title, str) or len(title.strip()) == 0:
            raise ValidationException("Trend title must be a non-empty string")
        
        if len(title) > 200:
            raise ValidationException("Trend title exceeds maximum length")
        
        # Validate description
        description = trend_data['description']
        if not isinstance(description, str):
            raise ValidationException("Trend description must be a string")
        
        if len(description) > 5000:
            raise ValidationException("Trend description exceeds maximum length")
        
        return True
    
    @staticmethod
    def sanitize_content(content: str) -> str:
        """
        Sanitize content for safe storage and display
        
        Args:
            content: Raw content string
            
        Returns:
            Sanitized content string
        """
        if not isinstance(content, str):
            return ""
        
        # Remove null bytes and other problematic characters
        content = content.replace('\x00', '')
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Remove or escape potentially dangerous HTML/JavaScript
        # Note: For production, consider using a proper HTML sanitization library
        content = content.replace('<script', '&lt;script')
        content = content.replace('javascript:', 'javascript-disabled:')
        
        return content
    
    @staticmethod
    def validate_search_query(query: str, max_length: int = 500) -> bool:
        """
        Validate search query input
        
        Args:
            query: Search query string
            max_length: Maximum allowed length
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(query, str):
            raise ValidationException("Search query must be a string")
        
        if len(query) > max_length:
            raise ValidationException(f"Search query exceeds maximum length of {max_length}")
        
        # Check for potentially problematic patterns
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValidationException("Search query contains potentially dangerous content")
        
        return True
    
    @staticmethod
    def validate_pagination_params(page: Any, per_page: Any) -> tuple[int, int]:
        """
        Validate and normalize pagination parameters
        
        Args:
            page: Page number
            per_page: Items per page
            
        Returns:
            Tuple of (page, per_page) as integers
        """
        # Validate page
        try:
            page = int(page) if page else 1
        except (ValueError, TypeError):
            page = 1
        
        if page < 1:
            page = 1
        elif page > 1000:  # Reasonable upper limit
            page = 1000
        
        # Validate per_page
        try:
            per_page = int(per_page) if per_page else 10
        except (ValueError, TypeError):
            per_page = 10
        
        if per_page < 1:
            per_page = 10
        elif per_page > 100:  # Reasonable upper limit
            per_page = 100
        
        return page, per_page

# Global validator instance
data_validator = DataValidator()