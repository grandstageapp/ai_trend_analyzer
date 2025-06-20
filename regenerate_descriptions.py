#!/usr/bin/env python3
"""
Script to regenerate trend descriptions using proper AI generation
"""
import os
import sys
sys.path.append('.')

from app import create_app, db
from models import Trend, Post, PostTrend
from services.openai_service import OpenAIService

def regenerate_trend_descriptions():
    """Regenerate all trend descriptions using the proper AI service"""
    app = create_app()
    with app.app_context():
        openai_service = OpenAIService()
        trends = Trend.query.all()
        
        print(f"Found {len(trends)} trends to regenerate descriptions for...")
        
        for trend in trends:
            print(f"\nRegenerating description for: {trend.title}")
            
            # Get related posts for context
            related_posts = db.session.query(Post).join(PostTrend).filter(
                PostTrend.trend_id == trend.id
            ).limit(10).all()
            
            if related_posts:
                post_contents = [post.content for post in related_posts]
                print(f"Using {len(post_contents)} related posts for context")
                
                # Generate new description
                new_description = openai_service.generate_trend_description(
                    trend.title, 
                    post_contents
                )
                
                if new_description and len(new_description) > 100:
                    trend.description = new_description
                    print(f"Generated description ({len(new_description)} chars)")
                else:
                    print("Failed to generate description or description too short")
            else:
                print("No related posts found for context")
        
        # Commit all changes
        db.session.commit()
        print("\nAll trend descriptions regenerated successfully!")

if __name__ == "__main__":
    regenerate_trend_descriptions()