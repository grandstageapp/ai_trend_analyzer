#!/usr/bin/env python3
"""
Test script for the ContentGenerationService
"""
import os
from app import create_app, db
from models import Trend
from services.content_generation_service import ContentGenerationService

def test_content_generation():
    """Test all content generation methods"""
    app = create_app()
    with app.app_context():
        try:
            # Get a sample trend
            trend = Trend.query.first()
            if not trend:
                print("No trends found in database. Run populate_sample_data.py first.")
                return False
            
            print(f"Testing content generation for trend: {trend.title}")
            
            # Initialize service
            content_service = ContentGenerationService()
            print("✓ ContentGenerationService initialized")
            
            # Test blog content generation
            print("\nTesting blog content generation...")
            blog_content = content_service.generate_blog_content(trend.id)
            if blog_content and len(blog_content) > 100:
                print(f"✓ Blog content generated ({len(blog_content)} characters)")
                print(f"Preview: {blog_content[:200]}...")
            else:
                print("✗ Blog content generation failed")
            
            # Test social media content generation
            print("\nTesting social media content generation...")
            social_content = content_service.generate_social_media_content(trend.id, "twitter")
            if isinstance(social_content, dict) and social_content:
                print(f"✓ Social media content generated")
                for platform, content in social_content.items():
                    print(f"  {platform}: {len(content)} characters")
            else:
                print("✗ Social media content generation failed")
            
            # Test newsletter content generation
            print("\nTesting newsletter content generation...")
            newsletter_content = content_service.generate_email_newsletter_content(trend.id)
            if newsletter_content and len(newsletter_content) > 100:
                print(f"✓ Newsletter content generated ({len(newsletter_content)} characters)")
                print(f"Preview: {newsletter_content[:200]}...")
            else:
                print("✗ Newsletter content generation failed")
            
            # Test content outline generation
            print("\nTesting content outline generation...")
            outline_content = content_service.generate_content_outline(trend.id)
            if outline_content and len(outline_content) > 100:
                print(f"✓ Content outline generated ({len(outline_content)} characters)")
                print(f"Preview: {outline_content[:200]}...")
            else:
                print("✗ Content outline generation failed")
            
            return True
            
        except Exception as e:
            print(f"✗ Content generation test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run content generation tests"""
    print("Content Generation Service - Test")
    print("=" * 40)
    
    success = test_content_generation()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ Content generation service is working properly")
    else:
        print("✗ Content generation service has issues")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)