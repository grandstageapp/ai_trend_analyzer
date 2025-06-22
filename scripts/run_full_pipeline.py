#!/usr/bin/env python3
"""
Run the complete end-to-end AI trends analysis pipeline
This will collect real Twitter data and generate trends
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from services.twitter_service import TwitterService
from services.trend_service import TrendService
from services.openai_service import OpenAIService
from models import Post, Author, Trend, TrendScore, Engagement, PostTrend
from config import Config

def run_data_collection():
    """Collect fresh data from Twitter"""
    print("="*60)
    print("STEP 1: COLLECTING FRESH TWITTER DATA")
    print("="*60)
    
    try:
        twitter_service = TwitterService()
        config = Config()
        
        # Use AI search terms from config
        search_terms = config.AI_SEARCH_TERMS
        print(f"Searching for: {search_terms}")
        
        posts = twitter_service.search_recent_posts(
            search_terms=search_terms,
            max_results=50  # Collect more posts for better trend analysis
        )
        
        if not posts:
            print("❌ No posts collected from Twitter")
            return False
        
        print(f"✓ Collected {len(posts)} posts from Twitter")
        
        # Store posts in database
        stored_count = 0
        for post_data in posts:
            try:
                # Check if author exists
                author_username = post_data['author']['username']
                author = Author.query.filter_by(username=author_username).first()
                
                if not author:
                    # Create new author
                    author = Author(
                        username=author_username,
                        author_name=post_data['author']['name'],
                        profile_url=post_data['author']['profile_url'],
                        follower_count=post_data['author']['follower_count'],
                        verified=post_data['author']['verified']
                    )
                    db.session.add(author)
                    db.session.flush()  # Get the ID
                
                # Check if post already exists
                existing_post = Post.query.filter_by(post_id=post_data['id']).first()
                if existing_post:
                    continue
                
                # Create new post
                post = Post(
                    post_id=post_data['id'],
                    author_id=author.id,
                    content=post_data['content'],
                    publish_date=post_data['publish_date']
                )
                db.session.add(post)
                db.session.flush()  # Get the ID
                
                # Add engagement data
                engagement = Engagement(
                    post_id=post.id,
                    like_count=post_data['metrics']['like_count'],
                    comment_count=post_data['metrics']['reply_count'],
                    repost_count=post_data['metrics']['retweet_count']
                )
                db.session.add(engagement)
                
                stored_count += 1
                
            except Exception as e:
                print(f"⚠️  Error storing post {post_data.get('id', 'unknown')}: {e}")
                continue
        
        db.session.commit()
        print(f"✓ Stored {stored_count} new posts in database")
        return True
        
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_trend_analysis():
    """Analyze posts and generate trends"""
    print("\n" + "="*60)
    print("STEP 2: ANALYZING POSTS AND GENERATING TRENDS")
    print("="*60)
    
    try:
        trend_service = TrendService()
        
        # Get recent posts for analysis (last 7 days)
        from datetime import datetime, timedelta
        since_date = datetime.utcnow() - timedelta(days=7)
        
        posts = Post.query.filter(Post.publish_date >= since_date).all()
        print(f"Analyzing {len(posts)} recent posts...")
        
        if len(posts) < 5:
            print("⚠️  Not enough posts for trend analysis")
            return False
        
        # Run trend analysis
        trends_created = trend_service.analyze_and_create_trends(posts)
        
        if trends_created:
            print(f"✓ Generated {len(trends_created)} new trends")
            
            # Display created trends
            for trend in trends_created:
                score = trend.get_latest_score()
                print(f"  - {trend.title} (Score: {score:.2f})")
            
            return True
        else:
            print("⚠️  No new trends were generated")
            return False
            
    except Exception as e:
        print(f"❌ Trend analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def display_results():
    """Display final results and statistics"""
    print("\n" + "="*60)
    print("STEP 3: PIPELINE RESULTS")
    print("="*60)
    
    try:
        # Count total records
        total_posts = Post.query.count()
        total_authors = Author.query.count()
        total_trends = Trend.query.count()
        total_engagements = Engagement.query.count()
        
        print(f"Database Statistics:")
        print(f"  Posts: {total_posts}")
        print(f"  Authors: {total_authors}")
        print(f"  Trends: {total_trends}")
        print(f"  Engagement Records: {total_engagements}")
        
        # Show recent trends
        recent_trends = Trend.query.order_by(Trend.created_at.desc()).limit(5).all()
        
        if recent_trends:
            print(f"\nTop 5 Recent Trends:")
            for i, trend in enumerate(recent_trends, 1):
                score = trend.get_latest_score()
                post_count = db.session.query(PostTrend).filter_by(trend_id=trend.id).count()
                print(f"  {i}. {trend.title}")
                print(f"     Score: {score:.2f} | Posts: {post_count} | Created: {trend.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        # Show engagement stats
        from sqlalchemy import func
        engagement_stats = db.session.query(
            func.sum(Engagement.like_count).label('total_likes'),
            func.sum(Engagement.comment_count).label('total_comments'),
            func.sum(Engagement.repost_count).label('total_reposts')
        ).first()
        
        if engagement_stats and engagement_stats.total_likes:
            print(f"\nTotal Engagement:")
            print(f"  Likes: {engagement_stats.total_likes:,}")
            print(f"  Comments: {engagement_stats.total_comments:,}")
            print(f"  Reposts: {engagement_stats.total_reposts:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error displaying results: {e}")
        return False

def main():
    """Run the complete pipeline"""
    print("AI TRENDS ANALYZER - FULL PIPELINE EXECUTION")
    print("="*60)
    print("This will collect real Twitter data and generate AI trends")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        # Step 1: Data Collection
        collection_success = run_data_collection()
        
        # Step 2: Trend Analysis (only if collection succeeded)
        analysis_success = False
        if collection_success:
            analysis_success = run_trend_analysis()
        
        # Step 3: Display Results
        display_results()
        
        print("\n" + "="*60)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*60)
        
        if collection_success and analysis_success:
            print("✅ FULL PIPELINE COMPLETED SUCCESSFULLY!")
            print("The AI Trends Analyzer now has fresh data and trends.")
        elif collection_success:
            print("⚠️  PARTIAL SUCCESS - Data collected but trend analysis had issues")
        else:
            print("❌ PIPELINE FAILED - Unable to collect Twitter data")
        
        print("="*60)

if __name__ == "__main__":
    main()