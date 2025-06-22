#!/usr/bin/env python3
"""
Populate the database with sample trend data for demonstration
"""
import os
from datetime import datetime, timedelta
from app import create_app, db
from models import Author, Post, Engagement, Trend, TrendScore, PostTrend

def create_sample_data():
    """Create sample data for demonstration"""
    app = create_app()
    with app.app_context():
        # Clear existing data
        db.session.query(PostTrend).delete()
        db.session.query(TrendScore).delete()
        db.session.query(Engagement).delete()
        db.session.query(Post).delete()
        db.session.query(Author).delete()
        db.session.query(Trend).delete()
        db.session.commit()
        
        # Create sample authors
        authors = [
            Author(username="ai_researcher", author_name="Dr. Sarah Chen", follower_count=15000),
            Author(username="tech_analyst", author_name="Mike Johnson", follower_count=8500),
            Author(username="openai_updates", author_name="OpenAI News", follower_count=250000),
            Author(username="ai_ethicist", author_name="Prof. Maria Garcia", follower_count=12000),
            Author(username="startup_founder", author_name="Alex Kim", follower_count=5200)
        ]
        
        for author in authors:
            db.session.add(author)
        db.session.commit()
        
        # Create sample trends
        trends = [
            Trend(
                title="GPT-5 Development", 
                description="Latest developments and speculation around GPT-5 capabilities, release timeline, and potential impact on AI industry",
                total_posts=12
            ),
            Trend(
                title="AI Safety Regulations", 
                description="Government and industry discussions about AI safety standards, regulations, and ethical guidelines",
                total_posts=8
            ),
            Trend(
                title="Multimodal AI Advances", 
                description="Progress in AI models that can process text, images, video, and audio simultaneously",
                total_posts=15
            ),
            Trend(
                title="Enterprise AI Adoption", 
                description="How businesses are integrating AI tools into their workflows and operations",
                total_posts=10
            ),
            Trend(
                title="AI Model Optimization", 
                description="Techniques for making AI models more efficient, faster, and cost-effective",
                total_posts=6
            )
        ]
        
        for trend in trends:
            db.session.add(trend)
        db.session.commit()
        
        # Create sample posts
        sample_posts = [
            {
                "post_id": "1750001",
                "author_id": authors[0].id,
                "content": "Fascinating new research on transformer architecture improvements. The efficiency gains are remarkable - 40% faster inference with similar accuracy. #AI #MachineLearning",
                "trend_id": trends[4].id,
                "likes": 120,
                "comments": 15,
                "reposts": 8
            },
            {
                "post_id": "1750002", 
                "author_id": authors[1].id,
                "content": "Major tech companies are now requiring AI ethics training for all developers. This is a huge step forward for responsible AI development. #AIEthics #TechPolicy",
                "trend_id": trends[1].id,
                "likes": 89,
                "comments": 23,
                "reposts": 12
            },
            {
                "post_id": "1750003",
                "author_id": authors[2].id,
                "content": "Breaking: New multimodal AI can now process video, audio, and text simultaneously with unprecedented accuracy. Game-changing capabilities for content creation.",
                "trend_id": trends[2].id,
                "likes": 450,
                "comments": 67,
                "reposts": 89
            },
            {
                "post_id": "1750004",
                "author_id": authors[3].id,
                "content": "60% of Fortune 500 companies have now integrated AI into their core business processes. The transformation is accelerating faster than predicted.",
                "trend_id": trends[3].id,
                "likes": 200,
                "comments": 34,
                "reposts": 45
            },
            {
                "post_id": "1750005",
                "author_id": authors[4].id,
                "content": "GPT-5 rumors are heating up. Sources suggest 10x improvement in reasoning capabilities. If true, this could revolutionize how we think about AI applications.",
                "trend_id": trends[0].id,
                "likes": 300,
                "comments": 55,
                "reposts": 67
            }
        ]
        
        posts_objects = []
        for post_data in sample_posts:
            post = Post(
                post_id=post_data["post_id"],
                author_id=post_data["author_id"],
                content=post_data["content"],
                publish_date=datetime.utcnow() - timedelta(hours=2)
            )
            db.session.add(post)
            db.session.flush()
            posts_objects.append(post)
            
            # Add engagement
            engagement = Engagement(
                post_id=post.id,
                like_count=post_data["likes"],
                comment_count=post_data["comments"],
                repost_count=post_data["reposts"],
                timestamp=datetime.utcnow()
            )
            db.session.add(engagement)
            
            # Link post to trend
            post_trend = PostTrend(
                post_id=post.id,
                trend_id=post_data["trend_id"]
            )
            db.session.add(post_trend)
        
        db.session.commit()
        
        # Create trend scores
        for i, trend in enumerate(trends):
            # Calculate sample scores based on engagement
            base_score = 50 + (i * 10)  # Different base scores for variety
            
            # Add some score history
            for days_ago in range(7, 0, -1):
                score_date = datetime.utcnow() - timedelta(days=days_ago)
                score_value = base_score + (days_ago * 2) + (i * 5)  # Trending upward
                
                trend_score = TrendScore(
                    trend_id=trend.id,
                    score=score_value,
                    date_generated=score_date
                )
                db.session.add(trend_score)
        
        db.session.commit()
        
        print(f"✓ Created {len(authors)} sample authors")
        print(f"✓ Created {len(trends)} sample trends")
        print(f"✓ Created {len(sample_posts)} sample posts")
        print(f"✓ Created engagement and trend score data")
        print("✓ Sample data population complete")

if __name__ == "__main__":
    create_sample_data()