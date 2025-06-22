#!/usr/bin/env python3
"""
Test Twitter API connectivity with updated credentials
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from services.twitter_service import TwitterService
from config import Config

def test_twitter_api():
    """Test Twitter API authentication and basic functionality"""
    
    print("Testing Twitter API with updated credentials...")
    
    # Check if API keys are available
    config = Config()
    required_keys = [
        'X_API_KEY',
        'X_API_SECRET', 
        'X_ACCESS_TOKEN',
        'X_ACCESS_TOKEN_SECRET',
        'X_BEARER_TOKEN'
    ]
    
    missing_keys = []
    for key in required_keys:
        value = getattr(config, key, None)
        if not value:
            missing_keys.append(key)
        else:
            print(f"✓ {key}: Present ({value[:12]}...)")
    
    if missing_keys:
        print(f"❌ Missing API keys: {', '.join(missing_keys)}")
        return False
    
    print("\n" + "="*50)
    print("Testing Twitter Service initialization...")
    
    try:
        twitter_service = TwitterService()
        print("✓ Twitter service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Twitter service: {e}")
        return False
    
    print("\n" + "="*50)
    print("Testing Twitter API search...")
    
    try:
        # Test with AI search terms
        test_terms = ["AI", "artificial intelligence"]
        max_results = 10
        
        print(f"Searching for: {test_terms} (max {max_results} results)")
        
        posts = twitter_service.search_recent_posts(
            search_terms=test_terms,
            max_results=max_results
        )
        
        if posts:
            print(f"✓ Successfully retrieved {len(posts)} posts")
            print("\nSample post data:")
            sample_post = posts[0]
            print(f"  Post ID: {sample_post.get('id', 'N/A')}")
            print(f"  Author: @{sample_post.get('author', {}).get('username', 'N/A')}")
            print(f"  Content: {sample_post.get('content', 'N/A')[:100]}...")
            print(f"  Published: {sample_post.get('publish_date', 'N/A')}")
            
            # Check metrics data
            metrics = sample_post.get('metrics', {})
            if metrics:
                print(f"  Likes: {metrics.get('like_count', 0)}")
                print(f"  Replies: {metrics.get('reply_count', 0)}")
                print(f"  Retweets: {metrics.get('retweet_count', 0)}")
            
            return True
        else:
            print("⚠️  No posts retrieved - this might be normal if no recent verified posts match the search")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"❌ Twitter API search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limits():
    """Test rate limit information"""
    
    print("\n" + "="*50)
    print("Testing rate limit information...")
    
    try:
        twitter_service = TwitterService()
        rate_limit_info = twitter_service.get_rate_limit_status()
        
        if rate_limit_info:
            print("✓ Rate limit information retrieved:")
            remaining = rate_limit_info.get('remaining', 'N/A')
            limit = rate_limit_info.get('limit', 'N/A')
            reset_time = rate_limit_info.get('reset_time', 'N/A')
            if reset_time != 'N/A':
                from datetime import datetime
                reset_str = datetime.fromtimestamp(reset_time).strftime('%H:%M:%S')
            else:
                reset_str = 'N/A'
            print(f"  Search endpoint: {remaining}/{limit} remaining (resets at: {reset_str})")
        else:
            print("⚠️  No rate limit information available")
            
    except Exception as e:
        print(f"❌ Failed to get rate limit info: {e}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Twitter API Connectivity Test")
        print("="*50)
        
        success = test_twitter_api()
        test_rate_limits()
        
        print("\n" + "="*50)
        if success:
            print("✅ Twitter API test completed successfully!")
            print("The updated API keys are working and data collection should function properly.")
        else:
            print("❌ Twitter API test failed!")
            print("There may be an issue with the API keys or Twitter API access.")
        
        print("="*50)