import os
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TwitterService:
    """Service for interacting with X/Twitter API"""
    
    def __init__(self):
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
            # Check rate limit first
            rate_limit = self.get_rate_limit_status()
            if int(rate_limit.get('remaining', 0)) <= 0:
                reset_time = int(rate_limit.get('reset_time', 0))
                current_time = int(datetime.utcnow().timestamp())
                wait_time = reset_time - current_time
                logger.warning(f"Rate limit exceeded. Reset in {wait_time} seconds at {datetime.fromtimestamp(reset_time)}")
                return []
            
            # Build search query with OR operators
            query = " OR ".join([f'"{term}"' for term in search_terms])
            
            # Add filters for recent posts (24 hours) and English language
            since_time = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
            query += f" lang:en -is:retweet"
            
            # API parameters
            params = {
                "query": query,
                "max_results": min(max_results, 100),  # API limit is 100
                "start_time": since_time,
                "tweet.fields": "created_at,public_metrics,author_id,text,id",
                "user.fields": "id,username,name,public_metrics,profile_image_url",
                "expansions": "author_id"
            }
            
            url = f"{self.base_url}/tweets/search/recent"
            
            logger.info(f"Searching Twitter for: {query}")
            response = requests.get(url, headers=self.headers, params=params)
            
            # Cache rate limit info from response headers
            self._cached_rate_info = {
                'remaining': response.headers.get('x-rate-limit-remaining', '0'),
                'reset_time': response.headers.get('x-rate-limit-reset', '0'),
                'limit': response.headers.get('x-rate-limit-limit', '1')
            }
            
            if response.status_code == 200:
                data = response.json()
                posts = self._process_search_response(data)
                logger.info(f"Retrieved {len(posts)} posts from Twitter")
                return posts
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded during search")
                return []
            else:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Twitter posts: {e}")
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
        
        if 'data' not in data:
            return posts
        
        # Create user lookup dictionary
        users = {}
        if 'includes' in data and 'users' in data['includes']:
            for user in data['includes']['users']:
                users[user['id']] = user
        
        for tweet in data['data']:
            try:
                author_info = users.get(tweet['author_id'], {})
                
                post = {
                    'post_id': tweet['id'],
                    'content': tweet['text'],
                    'created_at': datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                    'author': {
                        'id': tweet['author_id'],
                        'username': author_info.get('username', 'unknown'),
                        'name': author_info.get('name', 'Unknown'),
                        'follower_count': author_info.get('public_metrics', {}).get('followers_count', 0),
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
        Get rate limit status from the last API response headers
        This doesn't consume API quota - it uses cached info from previous requests
        
        Returns:
            Rate limit information
        """
        # Return cached rate limit info if available
        if hasattr(self, '_cached_rate_info'):
            return self._cached_rate_info
        
        # If no cached info, assume we need to make a request to get initial status
        # This will be updated after the first actual API call
        return {
            'remaining': '1',  # Assume we have quota until proven otherwise
            'reset_time': str(int(datetime.utcnow().timestamp()) + 900),  # 15 minutes from now
            'limit': '1'
        }
