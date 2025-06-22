#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Trend, Post, PostTrend
from services.openai_service import OpenAIService

def update_descriptions():
    app = create_app()
    with app.app_context():
        openai_service = OpenAIService()
        trends = Trend.query.all()
        
        for trend in trends:
            print(f"Updating: {trend.title}")
            
            # Get related posts
            related_posts = db.session.query(Post).join(PostTrend).filter(
                PostTrend.trend_id == trend.id
            ).limit(8).all()
            
            post_contents = [post.content for post in related_posts]
            
            try:
                new_description = openai_service.generate_trend_description(
                    trend.title, post_contents
                )
                
                if new_description and len(new_description) > 100:
                    trend.description = new_description
                    db.session.commit()
                    print(f"✓ {trend.title} ({len(new_description)} chars)")
                else:
                    print(f"✗ Failed: {trend.title}")
                    
            except Exception as e:
                print(f"✗ Error {trend.title}: {e}")
        
        print("Done!")

if __name__ == "__main__":
    update_descriptions()