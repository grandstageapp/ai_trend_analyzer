import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class TwitterService:
    """Service for interacting with X/Twitter API"""
    
    def __init__(self):
        self.config = Config()
        self.bearer_token = os.environ.get('X_BEARER_TOKEN')
        self.api_key = os.environ.get('X_API_KEY') 
        self.api_secret = os.environ.get('X_API_SECRET')
        self.access_token = os.environ.get('X_ACCESS_TOKEN')
        self.access_token_secret = os.environ.get('X_ACCESS_TOKEN_SECRET')
        
        if not self.bearer_token:
            logger.error("X_BEARER_TOKEN environment variable not set")
            raise ValueError("Twitter API credentials not configured")
        
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
    
    def search_recent_posts(self, search_terms: List[str], max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for recent posts using the Recent Search API endpoint
        
        Args:
            search_terms: List of terms to search for (will be ORed together)
            max_results: Maximum number of results to return (10-100)
            
        Returns:
            List of post dictionaries
        """
        try:
            # Check rate limit first (only if we have cached info)
            if hasattr(self, '_cached_rate_info'):
                rate_limit = self.get_rate_limit_status()
                remaining = int(rate_limit.get('remaining', 1))
                if remaining <= 0:
                    reset_time = int(rate_limit.get('reset_time', 0))
                    current_time = int(datetime.utcnow().timestamp())
                    wait_time = reset_time - current_time
                    logger.warning(f"Rate limit exceeded. Reset in {wait_time} seconds at {datetime.fromtimestamp(reset_time)}")
                    return []
            
            # Build search query with OR operators - simplified for better success rate
            query = " OR ".join([f'"{term}"' for term in search_terms])
            
            # Add minimal filters to reduce query complexity
            query += " lang:en -is:retweet"
            
            # Use 1 day for more recent and manageable results
            since_time = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
            
            # API parameters - simplified for better reliability
            params = {
                "query": query,
                "max_results": min(max_results, 10),  # Start with smaller batch
                "start_time": since_time,
                "tweet.fields": "created_at,public_metrics,author_id,text,id",
                "user.fields": "id,username,name,public_metrics",
                "expansions": "author_id"
            }
            
            url = f"{self.base_url}/tweets/search/recent"
            
            logger.info(f"Searching Twitter for: {query}")
            response = requests.get(url, headers=self.headers, params=params)
            
            # Cache rate limit info from response headers with proper data types
            try:
                self._cached_rate_info = {
                    'remaining': int(response.headers.get('x-rate-limit-remaining', '0')),
                    'reset_time': int(response.headers.get('x-rate-limit-reset', '0')),
                    'limit': int(response.headers.get('x-rate-limit-limit', '1'))
                }
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing rate limit headers: {e}")
                self._cached_rate_info = {'remaining': 0, 'reset_time': 0, 'limit': 1}
            
            if response.status_code == 200:
                data = response.json()
                
                # Log raw API response for debugging
                logger.debug(f"Raw Twitter API response: {json.dumps(data, indent=2)}")
                
                if 'data' not in data:
                    logger.warning("No data returned from Twitter API - possibly no matching tweets")
                    return []
                    
                # Log first tweet's raw data for debugging
                if data.get('data') and len(data['data']) > 0:
                    first_tweet = data['data'][0]
                    logger.info(f"Sample tweet raw data: {json.dumps(first_tweet, indent=2)}")
                
                posts = self._process_search_response(data)
                logger.info(f"Retrieved {len(posts)} posts from Twitter")
                return posts
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded during search")
                return []
            elif response.status_code == 400:
                logger.error(f"Bad request to Twitter API: {response.text}")
                return []
            elif response.status_code == 401:
                logger.error("Twitter API authentication failed - check API credentials")
                return []
            else:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error when searching Twitter posts: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching Twitter posts: {e}")
            return []
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by user ID
        
        Args:
            user_id: Twitter user ID
            
        Returns:
            User information dictionary or None
        """
        try:
            url = f"{self.base_url}/users/{user_id}"
            params = {
                "user.fields": "id,username,name,public_metrics,profile_image_url,description"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data')
            else:
                logger.error(f"Error fetching user {user_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            return None
    
    def _process_search_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process the Twitter API search response into a standardized format
        
        Args:
            data: Raw API response data
            
        Returns:
            List of processed post dictionaries
        """
        posts = []
        
        if 'data' not in data or not data['data']:
            logger.info("No tweet data found in API response")
            return posts
        
        # Create user lookup dictionary
        users = {}
        if 'includes' in data and 'users' in data['includes']:
            for user in data['includes']['users']:
                users[user['id']] = user
        
        for tweet in data['data']:
            try:
                # Validate required fields
                if not tweet.get('id') or not tweet.get('text') or not tweet.get('author_id'):
                    logger.warning(f"Skipping tweet with missing required fields: {tweet.get('id', 'unknown')}")
                    continue
                
                author_info = users.get(tweet['author_id'], {})
                
                # Parse created_at with proper error handling
                try:
                    created_at = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
                except (ValueError, KeyError):
                    logger.warning(f"Invalid created_at format for tweet {tweet['id']}, using current time")
                    created_at = datetime.utcnow()
                
                post = {
                    'post_id': tweet['id'],
                    'content': tweet['text'],
                    'created_at': created_at,
                    'author': {
                        'id': tweet['author_id'],
                        'username': author_info.get('username', 'unknown'),
                        'name': author_info.get('name', 'Unknown'),
                        'follower_count': author_info.get('public_metrics', {}).get('followers_count', 0),
                        'verified': author_info.get('verified', False),
                        'profile_url': f"https://twitter.com/{author_info.get('username', 'unknown')}"
                    },
                    'metrics': {
                        'like_count': tweet.get('public_metrics', {}).get('like_count', 0),
                        'retweet_count': tweet.get('public_metrics', {}).get('retweet_count', 0),
                        'reply_count': tweet.get('public_metrics', {}).get('reply_count', 0),
                        'quote_count': tweet.get('public_metrics', {}).get('quote_count', 0)
                    }
                }
                
                posts.append(post)
                
            except Exception as e:
                logger.error(f"Error processing tweet {tweet.get('id', 'unknown')}: {e}")
                continue
        
        return posts
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get rate limit status - tries to get fresh data from rate limit endpoint
        Falls back to cached info from previous requests
        
        Returns:
            Rate limit information with consistent data types
        """
        try:
            # Try to get fresh rate limit info (doesn't consume search quota)
            url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                search_info = data.get('resources', {}).get('search', {}).get('/search/tweets', {})
                
                if search_info:
                    fresh_info = {
                        'remaining': int(search_info.get('remaining', 0)),
                        'reset_time': int(search_info.get('reset', 0)),
                        'limit': int(search_info.get('limit', 1))
                    }
                    self._cached_rate_info = fresh_info
                    return fresh_info
        except Exception as e:
            logger.warning(f"Could not fetch fresh rate limit info: {e}")
        
        # Return cached rate limit info if available
        if hasattr(self, '_cached_rate_info'):
            return self._cached_rate_info
        
        # If no cached info, assume we have quota until proven otherwise
        return {
            'remaining': 1,
            'reset_time': int(datetime.utcnow().timestamp()) + 900,  # 15 minutes from now
            'limit': 1
        }
