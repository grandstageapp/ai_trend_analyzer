#!/usr/bin/env python3
"""
Manual data collection script for testing and immediate use
"""
import sys
from datetime import datetime
from tasks.background_tasks import BackgroundTasks
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run manual data collection"""
    print("=== Manual Data Collection ===")
    print(f"Started at: {datetime.now()}")
    
    try:
        task_runner = BackgroundTasks()
        
        # Check rate limit first
        from services.twitter_service import TwitterService
        from config import Config
        twitter = TwitterService()
        config = Config()
        rate_limit = twitter.get_rate_limit_status()
        remaining = rate_limit.get('remaining', 0)
        
        if remaining <= 0:
            reset_time = rate_limit.get('reset_time', 0)
            reset_datetime = datetime.fromtimestamp(reset_time)
            print(f"Rate limit exceeded. Next reset at {reset_datetime}")
            wait_minutes = (reset_time - datetime.now().timestamp()) / 60
            print(f"Please wait {wait_minutes:.1f} minutes before trying again")
            return 1
        
        print(f"Rate limit OK ({remaining} requests remaining)")
        print("Starting data collection...")
        
        # Run the data collection
        task_runner.fetch_and_process_posts()
        
        print("Data collection completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error during data collection: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())