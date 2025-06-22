#!/usr/bin/env python3
"""
Test end-to-end trend generation with real Twitter data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from services.twitter_service import TwitterService
from services.trend_service import TrendService
from models import Post, Author, Trend, Engagement, PostTrend
from datetime import datetime, timedelta

def test_data_collection():
    """Test collecting a small amount of real Twitter data"""
    print("Testing Twitter data collection...")
    
    try:
        twitter_service = TwitterService()
        
        # Small test - just get 10 posts
        posts = twitter_service.search_recent_posts(
            search_terms=["AI"],
            max_results=10
        )
        
        if posts:
            print(f"✓ Retrieved {len(posts)} posts from Twitter")
            
            # Show sample data
            sample = posts[0]
            print(f"Sample post: {sample['content'][:60]}...")
            print(f"Author: @{sample['author']['username']}")
            print(f"Metrics: {sample['metrics']['like_count']} likes")
            
            return posts
        else:
            print("❌ No posts retrieved")
            return []
            
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        return []

def test_trend_generation(posts_data):
    """Test trend generation with collected posts"""
    print("\nTesting trend generation...")
    
    if not posts_data:
        print("❌ No posts to analyze")
        return False
    
    try:
        # Store a few posts for analysis
        stored_posts = []
        
        for post_data in posts_data[:5]:  # Just store 5 posts for testing
            # Create or get author
            author_username = post_data['author']['username']
            author = Author.query.filter_by(username=author_username).first()
            
            if not author:
                author = Author(
                    username=author_username,
                    author_name=post_data['author']['name'],
                    profile_url=post_data['author']['profile_url'],
                    follower_count=post_data['author']['follower_count'],
                    verified=post_data['author']['verified']
                )
                db.session.add(author)
                db.session.flush()
            
            # Create post
            post = Post(
                post_id=post_data['id'],
                author_id=author.id,
                content=post_data['content'],
                publish_date=post_data['publish_date']
            )
            db.session.add(post)
            db.session.flush()
            
            # Add engagement
            engagement = Engagement(
                post_id=post.id,
                like_count=post_data['metrics']['like_count'],
                comment_count=post_data['metrics']['reply_count'],
                repost_count=post_data['metrics']['retweet_count']
            )
            db.session.add(engagement)
            
            stored_posts.append(post)
        
        db.session.commit()
        print(f"✓ Stored {len(stored_posts)} posts")
        
        # Try trend analysis
        trend_service = TrendService()
        trends = trend_service.analyze_and_create_trends(stored_posts)
        
        if trends:
            print(f"✓ Generated {len(trends)} trends")
            for trend in trends:
                score = trend.get_latest_score()
                print(f"  - {trend.title} (Score: {score:.2f})")
            return True
        else:
            print("⚠️  No trends generated (this is normal with small data)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"❌ Trend generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run end-to-end test"""
    print("AI Trends Analyzer - End-to-End Test")
    print("="*50)
    
    app = create_app()
    with app.app_context():
        # Test 1: Data Collection
        posts_data = test_data_collection()
        
        # Test 2: Trend Generation
        if posts_data:
            success = test_trend_generation(posts_data)
            
            if success:
                print("\n✅ End-to-end test completed successfully!")
                print("The system can collect real Twitter data and process it.")
            else:
                print("\n❌ End-to-end test failed during trend generation")
        else:
            print("\n❌ End-to-end test failed during data collection")
        
        print("="*50)

if __name__ == "__main__":
    main()