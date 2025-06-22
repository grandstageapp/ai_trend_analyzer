#!/usr/bin/env python3
"""
Script to regenerate detailed trend descriptions using OpenAI API
This will update all existing trends with comprehensive 200-500 word descriptions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Trend, Post, PostTrend
from services.openai_service import OpenAIService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_trend_descriptions():
    """Regenerate all trend descriptions with detailed content"""
    app = create_app()
    with app.app_context():
        try:
            # Initialize OpenAI service
            openai_service = OpenAIService()
            
            # Get all trends
            trends = Trend.query.all()
            logger.info(f"Found {len(trends)} trends to update")
            
            for trend in trends:
                logger.info(f"Updating description for trend: {trend.title}")
                
                # Get related posts for context
                related_posts = db.session.query(Post).join(PostTrend).filter(
                    PostTrend.trend_id == trend.id
                ).limit(10).all()
                
                post_contents = [post.content for post in related_posts]
                
                # Skip if description is already substantial (>300 characters)
                if len(trend.description) > 300:
                    logger.info(f"⏭ Skipping '{trend.title}' - already has detailed description ({len(trend.description)} chars)")
                    continue
                
                # Generate detailed description
                try:
                    new_description = openai_service.generate_trend_description(
                        trend.title, 
                        post_contents
                    )
                    
                    if new_description and len(new_description) > 100:  # Ensure it's substantial
                        trend.description = new_description
                        logger.info(f"✓ Updated description for '{trend.title}' ({len(new_description)} characters)")
                        # Commit after each successful update to avoid losing progress
                        db.session.commit()
                    else:
                        logger.warning(f"✗ Failed to generate description for '{trend.title}'")
                        
                except Exception as e:
                    logger.error(f"✗ Error generating description for '{trend.title}': {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            logger.info("✓ All trend descriptions updated successfully!")
            
            # Display updated trends
            print("\n" + "="*60)
            print("UPDATED TREND DESCRIPTIONS")
            print("="*60)
            
            for trend in trends:
                print(f"\nTrend: {trend.title}")
                print(f"Posts: {trend.total_posts}")
                print(f"Description length: {len(trend.description)} characters")
                print(f"Preview: {trend.description[:100]}...")
                print("-" * 40)
                
        except Exception as e:
            logger.error(f"Error updating trend descriptions: {e}")
            db.session.rollback()
            return False
            
        return True

if __name__ == "__main__":
    print("Regenerating trend descriptions with OpenAI...")
    success = regenerate_trend_descriptions()
    
    if success:
        print("\n✓ Trend descriptions regenerated successfully!")
    else:
        print("\n✗ Failed to regenerate trend descriptions")
        sys.exit(1)