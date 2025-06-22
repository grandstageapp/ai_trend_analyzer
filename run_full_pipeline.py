#!/usr/bin/env python3
"""
Full pipeline script to fetch Twitter data and analyze trends
This script runs the complete data collection and analysis pipeline
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from app import create_app, db
from models import Post, Author, Trend, TrendScore
from tasks.background_tasks import BackgroundTasks
from services.twitter_service import TwitterService
from services.trend_service import TrendService
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_twitter_api_connection():
    """Test Twitter API connection and wait for rate limit if needed"""
    print("=== Testing Twitter API Connection ===")
    
    try:
        # Check if API keys are available
        config = Config()
        bearer_token = config.X_BEARER_TOKEN
        api_key = config.X_API_KEY
        
        if not bearer_token and not api_key:
            print("❌ No Twitter API credentials found")
            print("Required: X_BEARER_TOKEN or (X_API_KEY + X_API_SECRET)")
            return False
            
        if bearer_token:
            print("✅ Bearer token found")
        if api_key:
            print("✅ API key found")
            
        # Initialize Twitter service
        twitter_service = TwitterService()
        
        # Get fresh rate limit info
        rate_limit = twitter_service.get_rate_limit_status()
        remaining = rate_limit.get('remaining', 0)
        reset_time = rate_limit.get('reset_time', 0)
        
        if remaining > 0:
            reset_datetime = datetime.fromtimestamp(reset_time) if reset_time else "unknown"
            print(f"✅ Rate limit OK: {remaining} requests remaining")
            print(f"   Reset time: {reset_datetime}")
            return True
        elif reset_time > 0:
            reset_datetime = datetime.fromtimestamp(reset_time)
            current_time = datetime.utcnow().timestamp()
            wait_seconds = reset_time - current_time
            
            if wait_seconds > 0:
                print(f"⏳ Rate limit exceeded. Reset at: {reset_datetime}")
                print(f"   Waiting {wait_seconds:.0f} seconds for reset...")
                import time
                time.sleep(wait_seconds + 5)  # Add 5 second buffer
                print("✅ Rate limit should be reset now")
                return True
            else:
                print("✅ Rate limit should be reset already")
                return True
        else:
            print("⚠️  Cannot determine rate limit status, proceeding with caution")
            return True
            
    except Exception as e:
        print(f"❌ Twitter API connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_status():
    """Check database connection and current data status"""
    print("\n=== Database Status Check ===")
    
    try:
        app = create_app()
        with app.app_context():
            # Check database connection
            db.session.execute(db.text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check current data counts
            author_count = Author.query.count()
            post_count = Post.query.count()
            trend_count = Trend.query.count()
            score_count = TrendScore.query.count()
            
            print(f"📊 Current database stats:")
            print(f"   Authors: {author_count}")
            print(f"   Posts: {post_count}")
            print(f"   Trends: {trend_count}")
            print(f"   Trend Scores: {score_count}")
            
            # Check for recent posts (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_posts = Post.query.filter(Post.created_at >= recent_cutoff).count()
            print(f"   Recent posts (last 7 days): {recent_posts}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def run_data_collection():
    """Run the data collection pipeline"""
    print("\n=== Running Data Collection Pipeline ===")
    
    try:
        app = create_app()
        with app.app_context():
            # Initialize background tasks
            task_runner = BackgroundTasks()
            
            # Check rate limit before proceeding
            twitter_service = TwitterService()
            rate_limit = twitter_service.get_rate_limit_status()
            remaining = rate_limit.get('remaining', 0)
            
            if remaining <= 0:
                reset_time = rate_limit.get('reset_time', 0)
                if reset_time > 0:
                    reset_datetime = datetime.fromtimestamp(reset_time)
                    print(f"❌ Rate limit exceeded. Next reset at {reset_datetime}")
                    wait_minutes = (reset_time - datetime.utcnow().timestamp()) / 60
                    print(f"   Please wait {wait_minutes:.1f} minutes before trying again")
                    return False
                else:
                    print("⚠️  Rate limit status unclear, proceeding with caution")
            else:
                print(f"✅ Rate limit OK ({remaining} requests remaining)")
            
            print("🔄 Starting data collection...")
            
            # Run the fetch and process pipeline
            task_runner.fetch_and_process_posts()
            
            print("✅ Data collection completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_trend_analysis():
    """Run trend analysis on collected data"""
    print("\n=== Running Trend Analysis ===")
    
    try:
        app = create_app()
        with app.app_context():
            # Initialize background tasks
            task_runner = BackgroundTasks()
            
            # Check if we have posts to analyze
            post_count = Post.query.count()
            if post_count == 0:
                print("❌ No posts available for trend analysis")
                return False
                
            print(f"📊 Analyzing {post_count} posts for trends...")
            
            # Run trend analysis via trend service
            from services.trend_service import TrendService
            trend_service = TrendService()
            
            # Get recent posts for analysis
            recent_posts = Post.query.order_by(Post.created_at.desc()).limit(50).all()
            trend_service.analyze_and_create_trends(recent_posts)
            
            # Calculate trend scores
            trend_service.calculate_trend_scores()
            
            print("✅ Trend analysis completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Trend analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_results_summary():
    """Show summary of collected data and trends"""
    print("\n=== Pipeline Results Summary ===")
    
    try:
        app = create_app()
        with app.app_context():
            # Get updated counts
            author_count = Author.query.count()
            post_count = Post.query.count()
            trend_count = Trend.query.count()
            score_count = TrendScore.query.count()
            
            print(f"📊 Final database stats:")
            print(f"   Authors: {author_count}")
            print(f"   Posts: {post_count}")
            print(f"   Trends: {trend_count}")
            print(f"   Trend Scores: {score_count}")
            
            # Show recent trends if any
            recent_trends = Trend.query.order_by(Trend.created_at.desc()).limit(5).all()
            if recent_trends:
                print(f"\n🔥 Recent trends:")
                for trend in recent_trends:
                    latest_score = trend.get_latest_score()
                    score_text = f" (score: {latest_score:.2f})" if latest_score else ""
                    print(f"   • {trend.title}{score_text}")
            
            # Show sample recent posts
            recent_posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
            if recent_posts:
                print(f"\n📝 Sample recent posts:")
                for post in recent_posts:
                    content_preview = post.content[:100] + "..." if len(post.content) > 100 else post.content
                    print(f"   • @{post.author.username}: {content_preview}")
                    
    except Exception as e:
        print(f"❌ Results summary failed: {e}")

def main():
    """Main pipeline execution"""
    print("=" * 60)
    print("AI TRENDS ANALYZER - FULL PIPELINE")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    success = True
    
    # Step 1: Test Twitter API connection
    if not test_twitter_api_connection():
        print("\n❌ Twitter API test failed. Cannot proceed with data collection.")
        return 1
    
    # Step 2: Check database status
    if not check_database_status():
        print("\n❌ Database check failed. Cannot proceed.")
        return 1
    
    # Step 3: Run data collection
    if not run_data_collection():
        print("\n❌ Data collection failed.")
        success = False
    
    # Step 4: Run trend analysis (even if data collection partially failed)
    if not run_trend_analysis():
        print("\n❌ Trend analysis failed.")
        success = False
    
    # Step 5: Show results
    show_results_summary()
    
    print(f"\n{'=' * 60}")
    if success:
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
    else:
        print("⚠️  PIPELINE COMPLETED WITH ERRORS")
    print(f"Finished at: {datetime.now()}")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())