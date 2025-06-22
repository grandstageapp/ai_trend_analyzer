#!/usr/bin/env python3
"""
Create historical trend score data for the past 10 business days
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Trend, TrendScore
from datetime import datetime, timedelta
import random

def create_historical_trend_data():
    """Create historical trend scores for the past 10 business days"""
    
    # Get all existing trends
    trends = Trend.query.all()
    if not trends:
        print("No trends found. Please create trends first.")
        return
    
    print(f"Creating historical data for {len(trends)} trends over 10 business days...")
    
    # Define trend evolution patterns for realistic data
    trend_patterns = {
        "GPT-4 Advancements": {
            "base_score": 2.1,
            "volatility": 0.3,
            "trend_direction": "upward",
            "events": [
                {"day": 7, "multiplier": 1.8, "reason": "Major GPT-4 update announcement"},
                {"day": 3, "multiplier": 1.4, "reason": "Positive benchmark results"}
            ]
        },
        "AI Ethics and Safety": {
            "base_score": 1.8,
            "volatility": 0.4,
            "trend_direction": "stable",
            "events": [
                {"day": 8, "multiplier": 2.2, "reason": "EU AI Act news"},
                {"day": 5, "multiplier": 1.6, "reason": "Safety framework announcement"}
            ]
        },
        "Machine Learning Breakthroughs": {
            "base_score": 1.5,
            "volatility": 0.25,
            "trend_direction": "upward",
            "events": [
                {"day": 6, "multiplier": 1.7, "reason": "New transformer architecture"},
                {"day": 2, "multiplier": 1.3, "reason": "Research publication"}
            ]
        },
        "AI in Healthcare": {
            "base_score": 2.8,
            "volatility": 0.35,
            "trend_direction": "upward",
            "events": [
                {"day": 9, "multiplier": 1.9, "reason": "FDA approval news"},
                {"day": 4, "multiplier": 1.5, "reason": "Clinical trial results"}
            ]
        },
        "Autonomous Vehicles": {
            "base_score": 3.2,
            "volatility": 0.45,
            "trend_direction": "volatile",
            "events": [
                {"day": 8, "multiplier": 2.1, "reason": "Tesla FSD milestone"},
                {"day": 6, "multiplier": 0.7, "reason": "Safety incident report"},
                {"day": 1, "multiplier": 1.6, "reason": "New deployment announcement"}
            ]
        },
        "AI Hardware Innovation": {
            "base_score": 1.9,
            "volatility": 0.3,
            "trend_direction": "upward",
            "events": [
                {"day": 7, "multiplier": 2.0, "reason": "NVIDIA earnings report"},
                {"day": 3, "multiplier": 1.4, "reason": "New chip announcement"}
            ]
        },
        "Enterprise AI Adoption": {
            "base_score": 2.4,
            "volatility": 0.2,
            "trend_direction": "steady_up",
            "events": [
                {"day": 5, "multiplier": 1.5, "reason": "Quarterly earnings reports"},
                {"day": 2, "multiplier": 1.3, "reason": "Enterprise survey results"}
            ]
        },
        "AI Research Publications": {
            "base_score": 1.6,
            "volatility": 0.4,
            "trend_direction": "stable",
            "events": [
                {"day": 9, "multiplier": 1.8, "reason": "Nature AI breakthrough"},
                {"day": 4, "multiplier": 1.2, "reason": "Conference proceedings"}
            ]
        },
        "AI Startups and Funding": {
            "base_score": 2.0,
            "volatility": 0.5,
            "trend_direction": "volatile",
            "events": [
                {"day": 6, "multiplier": 2.3, "reason": "Major funding round"},
                {"day": 8, "multiplier": 0.8, "reason": "Market uncertainty"},
                {"day": 1, "multiplier": 1.7, "reason": "IPO announcement"}
            ]
        },
        "AI Art and Creativity": {
            "base_score": 1.7,
            "volatility": 0.35,
            "trend_direction": "upward",
            "events": [
                {"day": 7, "multiplier": 1.9, "reason": "Major platform update"},
                {"day": 3, "multiplier": 1.4, "reason": "Artist adoption news"}
            ]
        }
    }
    
    # Calculate business days (excluding weekends)
    business_days = []
    current_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    days_found = 0
    while days_found < 10:
        # 0 = Monday, 6 = Sunday
        if current_date.weekday() < 5:  # Monday to Friday
            business_days.append(current_date)
            days_found += 1
        current_date -= timedelta(days=1)
    
    business_days.reverse()  # Oldest to newest
    
    # Clear existing trend scores to avoid duplicates
    TrendScore.query.delete()
    db.session.commit()
    
    created_scores = 0
    
    for trend in trends:
        pattern = trend_patterns.get(trend.title, {
            "base_score": 1.0,
            "volatility": 0.3,
            "trend_direction": "stable",
            "events": []
        })
        
        base_score = pattern["base_score"]
        volatility = pattern["volatility"]
        direction = pattern["trend_direction"]
        events = pattern["events"]
        
        for day_index, date in enumerate(business_days):
            # Calculate base trend movement
            if direction == "upward":
                trend_multiplier = 1.0 + (day_index * 0.05)
            elif direction == "downward":
                trend_multiplier = 1.0 - (day_index * 0.03)
            elif direction == "steady_up":
                trend_multiplier = 1.0 + (day_index * 0.02)
            elif direction == "volatile":
                trend_multiplier = 1.0 + random.uniform(-0.2, 0.2)
            else:  # stable
                trend_multiplier = 1.0 + random.uniform(-0.1, 0.1)
            
            # Apply random daily volatility
            daily_variance = random.uniform(1.0 - volatility, 1.0 + volatility)
            
            # Check for special events
            event_multiplier = 1.0
            for event in events:
                if day_index == (10 - event["day"]):  # Convert to index
                    event_multiplier = event["multiplier"]
                    break
            
            # Calculate final score
            final_score = base_score * trend_multiplier * daily_variance * event_multiplier
            
            # Ensure minimum score
            final_score = max(0.1, final_score)
            
            # Create trend score record
            trend_score = TrendScore(
                trend_id=trend.id,
                date_generated=date,
                score=round(final_score, 2)
            )
            db.session.add(trend_score)
            created_scores += 1
    
    db.session.commit()
    
    print(f"Created {created_scores} historical trend score records")
    
    # Show sample of historical data
    print("\nSample historical trend data:")
    sample_scores = db.session.query(TrendScore, Trend.title).join(
        Trend, TrendScore.trend_id == Trend.id
    ).order_by(TrendScore.date_generated.desc(), TrendScore.score.desc()).limit(15).all()
    
    for score, title in sample_scores:
        print(f"{score.date_generated.strftime('%Y-%m-%d')}: {title[:25]:<25} Score: {score.score}")
    
    # Show trend evolution for top trend
    top_trend = Trend.query.join(TrendScore).order_by(TrendScore.score.desc()).first()
    if top_trend:
        print(f"\nTrend evolution for '{top_trend.title}':")
        evolution = TrendScore.query.filter_by(trend_id=top_trend.id).order_by(TrendScore.date_generated).all()
        for score in evolution:
            print(f"  {score.date_generated.strftime('%Y-%m-%d')}: {score.score}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_historical_trend_data()