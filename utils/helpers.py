import re
from datetime import datetime, timedelta
from typing import Any, Optional, List
import logging

logger = logging.getLogger(__name__)

def format_number(num: int) -> str:
    """
    Format numbers with K, M suffixes for display
    
    Args:
        num: Number to format
        
    Returns:
        Formatted number string
    """
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return f"{num/1000:.1f}K"
    else:
        return f"{num/1000000:.1f}M"

def truncate_text(text: str, sentences: int = 2) -> str:
    """
    Truncate text to specified number of sentences
    
    Args:
        text: Text to truncate
        sentences: Number of sentences to keep
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    # Split by sentence ending punctuation
    sentence_endings = re.split(r'[.!?]+', text)
    
    if len(sentence_endings) <= sentences:
        return text
    
    # Take first N sentences and add back punctuation
    truncated = '. '.join(sentence_endings[:sentences])
    if truncated and not truncated.endswith('.'):
        truncated += '.'
    
    return truncated

def clean_tweet_text(text: str) -> str:
    """
    Clean tweet text by removing URLs, mentions, and extra whitespace
    
    Args:
        text: Raw tweet text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove mentions (optional - might want to keep for context)
    # text = re.sub(r'@[A-Za-z0-9_]+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def format_datetime(dt: datetime, format_type: str = 'relative') -> str:
    """
    Format datetime for display
    
    Args:
        dt: Datetime to format
        format_type: 'relative', 'short', or 'full'
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return ""
    
    now = datetime.utcnow()
    
    if format_type == 'relative':
        diff = now - dt
        
        if diff.days > 30:
            return dt.strftime('%b %d, %Y')
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    elif format_type == 'short':
        return dt.strftime('%b %d, %Y')
    
    else:  # full
        return dt.strftime('%B %d, %Y at %I:%M %p')

def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text
    
    Args:
        text: Text to extract hashtags from
        
    Returns:
        List of hashtags (without #)
    """
    if not text:
        return []
    
    hashtags = re.findall(r'#(\w+)', text)
    return list(set(hashtags))  # Remove duplicates

def extract_mentions(text: str) -> List[str]:
    """
    Extract mentions from text
    
    Args:
        text: Text to extract mentions from
        
    Returns:
        List of usernames (without @)
    """
    if not text:
        return []
    
    mentions = re.findall(r'@(\w+)', text)
    return list(set(mentions))  # Remove duplicates

def calculate_engagement_rate(likes: int, comments: int, reposts: int, followers: int) -> float:
    """
    Calculate engagement rate as a percentage
    
    Args:
        likes: Number of likes
        comments: Number of comments
        reposts: Number of reposts
        followers: Number of followers
        
    Returns:
        Engagement rate as percentage
    """
    if followers == 0:
        return 0.0
    
    total_engagement = likes + comments + reposts
    return (total_engagement / followers) * 100

def validate_api_response(response_data: Any, required_fields: List[str]) -> bool:
    """
    Validate API response has required fields
    
    Args:
        response_data: API response data
        required_fields: List of required field names
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(response_data, dict):
        return False
    
    for field in required_fields:
        if field not in response_data:
            logger.warning(f"Missing required field: {field}")
            return False
    
    return True

def safe_get(data: dict, key: str, default: Any = None, data_type: type = str) -> Any:
    """
    Safely get value from dictionary with type conversion
    
    Args:
        data: Dictionary to get value from
        key: Key to look up
        default: Default value if key not found
        data_type: Type to convert to
        
    Returns:
        Value converted to specified type or default
    """
    try:
        value = data.get(key, default)
        if value is None:
            return default
        
        if data_type == str:
            return str(value)
        elif data_type == int:
            return int(float(value))  # Handle string numbers
        elif data_type == float:
            return float(value)
        elif data_type == bool:
            return bool(value)
        else:
            return value
            
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {key}={value} to {data_type}")
        return default

def generate_trend_slug(title: str) -> str:
    """
    Generate URL-friendly slug from trend title
    
    Args:
        title: Trend title
        
    Returns:
        URL-friendly slug
    """
    if not title:
        return ""
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    return slug

def parse_search_query(query: str) -> dict:
    """
    Parse search query and extract filters
    
    Args:
        query: Search query string
        
    Returns:
        Dictionary with parsed query components
    """
    result = {
        'terms': [],
        'hashtags': [],
        'mentions': [],
        'date_filter': None,
        'score_filter': None
    }
    
    if not query:
        return result
    
    # Extract special filters
    words = query.split()
    remaining_words = []
    
    for word in words:
        if word.startswith('#'):
            result['hashtags'].append(word[1:])
        elif word.startswith('@'):
            result['mentions'].append(word[1:])
        elif word.startswith('score:'):
            try:
                result['score_filter'] = float(word.split(':')[1])
            except (ValueError, IndexError):
                remaining_words.append(word)
        elif word.startswith('date:'):
            result['date_filter'] = word.split(':')[1]
        else:
            remaining_words.append(word)
    
    result['terms'] = remaining_words
    return result
