#!/usr/bin/env python3
"""
Test script to verify real Twitter data collection with rate limit handling
"""

import sys
import time
from datetime import datetime, timedelta
from app import create_app, db
from models import Post, Author
from services.twitter_service import TwitterService
from config import Config

def wait_for_rate_limit_reset():
    """Wait for Twitter API rate limit to reset"""
    print("Checking rate limit status...")
    
    try:
        twitter_service = TwitterService()
        rate_info = twitter_service.get_rate_limit_status()
        remaining = rate_info.get('remaining', 0)
        reset_time = rate_info.get('reset_time', 0)
        
        if remaining > 0:
            print(f"Rate limit OK: {remaining} requests available")
            return True
            
        if reset_time > 0:
            current_time = datetime.utcnow().timestamp()
            wait_seconds = reset_time - current_time
            
            if wait_seconds > 0:
                print(f"Rate limit exceeded. Waiting {wait_seconds:.0f} seconds for reset...")
                time.sleep(wait_seconds + 5)  # Add 5 second buffer
                return True
        
        print("Unable to determine rate limit status")
        return False
        
    except Exception as e:
        print(f"Error checking rate limit: {e}")
        return False

def test_real_data_collection():
    """Test collecting real data with proper rate limit handling"""
    print("=== Testing Real Twitter Data Collection ===")
    
    app = create_app()
    with app.app_context():
        # Clear existing sample data
        print("Clearing existing sample data...")
        initial_count = Post.query.count()
        print(f"Current posts in database: {initial_count}")
        
        if not wait_for_rate_limit_reset():
            print("Cannot proceed - rate limit issues")
            return False
            
        try:
            # Initialize services
            twitter_service = TwitterService()
            config = Config()
            
            # Make a simple test call with minimal query
            print("Making test API call with minimal query...")
            search_terms = ["AI"]  # Single term to reduce complexity
            posts_data = twitter_service.search_recent_posts(
                search_terms=search_terms,
                max_results=5  # Very small batch for testing
            )
            
            if not posts_data:
                print("No data returned from Twitter API")
                return False
                
            print(f"Successfully retrieved {len(posts_data)} real posts!")
            
            # Display sample of real data
            for i, post in enumerate(posts_data[:2]):
                print(f"\nReal Post {i+1}:")
                print(f"  Content: {post.get('content', 'No content')[:100]}...")
                print(f"  Author: {post.get('author', {}).get('username', 'No author')}")
                print(f"  Metrics: {post.get('metrics', {})}")
                
            return True
            
        except Exception as e:
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_real_data_collection()
    sys.exit(0 if success else 1)