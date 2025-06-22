#!/usr/bin/env python3
"""
Test script to collect real AI trend data and populate the database
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app import create_app, db
from models import Author, Post, Engagement, Trend, TrendScore
from services.twitter_service import TwitterService
from services.openai_service import OpenAIService
from services.trend_service import TrendService
from config import Config

def test_data_collection():
    """Test collecting real data from Twitter and analyzing trends"""
    print("Testing real data collection...")
    
    app = create_app()
    with app.app_context():
        try:
            # Initialize services
            twitter_service = TwitterService()
            openai_service = OpenAIService()
            trend_service = TrendService()
            config = Config()
            
            print("✓ Services initialized")
            
            # Fetch recent AI-related posts
            print("Fetching AI-related posts from Twitter...")
            search_terms = config.AI_SEARCH_TERMS[:config.SEARCH_TERMS_LIMIT]
            posts_data = twitter_service.search_recent_posts(
                search_terms=search_terms,
                max_results=config.DEFAULT_SEARCH_RESULTS
            )
            
            if not posts_data:
                print("✗ No posts retrieved from Twitter")
                return False
            
            print(f"✓ Retrieved {len(posts_data)} posts from Twitter")
            
            # Store a sample post to test database functionality
            if posts_data:
                sample_post = posts_data[0]
                print(f"Sample post: {sample_post.get('content', '')[:100]}...")
                
                # Test storing author
                author_data = sample_post.get('author', {})
                author = Author(
                    username=author_data.get('username', 'test_user'),
                    author_name=author_data.get('name', 'Test User'),
                    follower_count=author_data.get('follower_count', 0),
                    verified=author_data.get('verified', False)
                )
                db.session.add(author)
                db.session.commit()
                print("✓ Sample author stored")
                
                # Test storing post
                post = Post(
                    post_id=sample_post.get('post_id', 'test_123'),
                    author_id=author.id,
                    content=sample_post.get('content', 'Test content'),
                    publish_date=datetime.utcnow()
                )
                db.session.add(post)
                db.session.commit()
                print("✓ Sample post stored")
                
                # Test OpenAI embedding generation
                print("Testing OpenAI embedding generation...")
                embeddings = openai_service.generate_embeddings([post.content])
                if embeddings:
                    print(f"✓ Generated embedding with {len(embeddings[0])} dimensions")
                    
                    # Store embedding as comma-separated string
                    post.embedding = ','.join(map(str, embeddings[0]))
                    db.session.commit()
                    print("✓ Embedding stored in database")
                else:
                    print("✗ Failed to generate embeddings")
                
                # Test trend identification
                print("Testing AI trend identification...")
                trends = openai_service.cluster_and_identify_trends([{
                    'content': post.content,
                    'post_id': post.post_id
                }])
                
                if trends:
                    print(f"✓ Identified {len(trends)} potential trends")
                    for trend in trends[:2]:  # Show first 2 trends
                        print(f"  - {trend.get('title', 'Unknown')}: {trend.get('description', '')[:100]}...")
                else:
                    print("✗ No trends identified")
                
                # Clean up test data
                db.session.delete(post)
                db.session.delete(author)
                db.session.commit()
                print("✓ Test data cleaned up")
            
            return True
            
        except Exception as e:
            print(f"✗ Data collection test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run data collection test"""
    print("AI Trends Analyzer - Data Collection Test")
    print("=" * 50)
    
    success = test_data_collection()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ Data collection system is working properly")
        print("Ready to collect and analyze real AI trends")
    else:
        print("✗ Data collection system has issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)