#!/usr/bin/env python3
"""
Test real data collection from X API when quota is available
"""
import time
import logging
from datetime import datetime
from app import create_app, db
from models import Post, Author
from tasks.background_tasks import BackgroundTasks
from services.twitter_service import TwitterService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_quota():
    """Wait for API quota to be available"""
    twitter = TwitterService()
    
    while True:
        rate_limit = twitter.get_rate_limit_status()
        remaining = int(rate_limit.get('remaining', '0'))
        reset_time = int(rate_limit.get('reset_time', 0))
        current_time = int(datetime.utcnow().timestamp())
        
        if remaining > 0:
            print(f"Quota available: {remaining} requests")
            return True
            
        wait_seconds = reset_time - current_time
        if wait_seconds <= 0:
            print("Quota should be reset, checking again...")
            time.sleep(5)
            continue
            
        if wait_seconds > 300:  # More than 5 minutes
            print(f"Long wait required: {wait_seconds//60} minutes")
            return False
            
        print(f"Waiting {wait_seconds} seconds for quota reset...")
        time.sleep(wait_seconds + 5)

def test_collection():
    """Test the complete data collection pipeline"""
    with create_app().app_context():
        # Record initial state
        initial_posts = db.session.query(Post).count()
        initial_authors = db.session.query(Author).count()
        
        print(f"Initial state: {initial_posts} posts, {initial_authors} authors")
        
        # Run data collection
        task = BackgroundTasks()
        task.fetch_and_process_posts()
        
        # Check results
        final_posts = db.session.query(Post).count()
        final_authors = db.session.query(Author).count()
        
        new_posts = final_posts - initial_posts
        new_authors = final_authors - initial_authors
        
        print(f"Collection results: +{new_posts} posts, +{new_authors} authors")
        
        if new_posts > 0:
            # Show sample of new posts
            recent_posts = db.session.query(Post).filter(
                Post.created_at > datetime.utcnow().replace(hour=12, minute=45)
            ).limit(3).all()
            
            print("Sample collected posts:")
            for post in recent_posts:
                print(f"  - {post.content[:80]}... (@{post.author.username})")
                
        return new_posts > 0

if __name__ == "__main__":
    print("=== Real X API Data Collection Test ===")
    
    if wait_for_quota():
        success = test_collection()
        if success:
            print("SUCCESS: Real Twitter data collected and stored")
        else:
            print("FAILED: No data was collected")
    else:
        print("SKIPPED: Quota wait time too long")