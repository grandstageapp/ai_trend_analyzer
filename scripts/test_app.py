#!/usr/bin/env python3
"""
Simple test script to verify the AI Trends Analyzer is working
"""
import os
import sys
from datetime import datetime
from app import create_app, db
from models import Author, Post, Engagement, Trend, TrendScore

def test_database_connection():
    """Test database connection and table creation"""
    print("Testing database connection...")
    
    app = create_app()
    with app.app_context():
        try:
            # Test database connection
            db.session.execute(db.text("SELECT 1"))
            print("✓ Database connection successful")
            
            # Check if tables exist
            tables = db.inspector.get_table_names()
            expected_tables = ['authors', 'posts', 'engagement', 'trends', 'post_trends', 'trend_scores']
            
            for table in expected_tables:
                if table in tables:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing")
            
            # Test creating a sample author
            test_author = Author(
                username="test_user",
                author_name="Test User",
                follower_count=1000
            )
            db.session.add(test_author)
            db.session.commit()
            print("✓ Sample author created successfully")
            
            # Clean up
            db.session.delete(test_author)
            db.session.commit()
            print("✓ Test data cleaned up")
            
            return True
            
        except Exception as e:
            print(f"✗ Database test failed: {e}")
            return False

def test_api_keys():
    """Test if required API keys are available"""
    print("\nTesting API keys...")
    
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        print("✓ OpenAI API key found")
    else:
        print("✗ OpenAI API key missing")
    
    twitter_keys = [
        'X_BEARER_TOKEN',
        'X_API_KEY', 
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_TOKEN_SECRET'
    ]
    
    twitter_available = 0
    for key in twitter_keys:
        if os.environ.get(key):
            print(f"✓ {key} found")
            twitter_available += 1
        else:
            print(f"✗ {key} missing")
    
    if twitter_available >= 1:  # At least bearer token needed
        print("✓ Minimum Twitter API credentials available")
    else:
        print("✗ Twitter API credentials missing")

def test_services():
    """Test service initialization"""
    print("\nTesting services...")
    
    try:
        if os.environ.get('OPENAI_API_KEY'):
            from services.openai_service import OpenAIService
            openai_service = OpenAIService()
            print("✓ OpenAI service initialized")
        else:
            print("✗ OpenAI service cannot be initialized (missing API key)")
    except Exception as e:
        print(f"✗ OpenAI service failed: {e}")
    
    try:
        if os.environ.get('X_BEARER_TOKEN'):
            from services.twitter_service import TwitterService
            twitter_service = TwitterService()
            print("✓ Twitter service initialized")
        else:
            print("✗ Twitter service cannot be initialized (missing API key)")
    except Exception as e:
        print(f"✗ Twitter service failed: {e}")

def main():
    """Run all tests"""
    print("AI Trends Analyzer - System Test")
    print("=" * 40)
    
    # Test database
    db_success = test_database_connection()
    
    # Test API keys
    test_api_keys()
    
    # Test services
    test_services()
    
    print("\n" + "=" * 40)
    if db_success:
        print("✓ Core system is functional")
        print("Ready for API key configuration and data collection")
    else:
        print("✗ System has critical issues that need fixing")
    
    return db_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)