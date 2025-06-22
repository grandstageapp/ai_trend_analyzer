#!/usr/bin/env python3
"""
Simple scheduler for running background tasks
"""
import time
import schedule
import logging
from datetime import datetime
from tasks.background_tasks import BackgroundTasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_data_collection():
    """Run the data collection task"""
    try:
        logger.info("Starting scheduled data collection task")
        task_runner = BackgroundTasks()
        task_runner.fetch_and_process_posts()
        logger.info("Data collection task completed successfully")
    except Exception as e:
        logger.error(f"Error in scheduled data collection: {e}")

def run_trend_analysis():
    """Run the trend analysis task"""
    try:
        logger.info("Starting scheduled trend analysis task")
        task_runner = BackgroundTasks()
        task_runner.daily_trend_analysis()
        logger.info("Trend analysis task completed successfully")
    except Exception as e:
        logger.error(f"Error in scheduled trend analysis: {e}")

def check_rate_limit_and_schedule():
    """Check rate limit and only run collection if available"""
    from services.twitter_service import TwitterService
    
    try:
        twitter = TwitterService()
        rate_limit = twitter.get_rate_limit_status()
        remaining = int(rate_limit.get('remaining', 0))
        
        if remaining > 0:
            logger.info(f"Rate limit OK ({remaining} requests remaining), running data collection")
            run_data_collection()
        else:
            reset_time = int(rate_limit.get('reset_time', 0))
            reset_datetime = datetime.fromtimestamp(reset_time)
            logger.info(f"Rate limit exceeded. Next reset at {reset_datetime}")
            
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")

def main():
    """Main scheduler loop"""
    logger.info("Starting AI Trends Analyzer Scheduler")
    
    # Schedule tasks with rate limit awareness
    # Check rate limit every 2 hours and run collection if possible
    schedule.every(2).hours.do(check_rate_limit_and_schedule)
    
    # Run trend analysis once daily at 2 AM
    schedule.every().day.at("02:00").do(run_trend_analysis)
    
    # Run initial rate limit check
    logger.info("Running initial rate limit check...")
    check_rate_limit_and_schedule()
    
    # Also schedule a check in 15 minutes (after rate limit resets)
    schedule.every(15).minutes.do(check_rate_limit_and_schedule)
    
    logger.info("Scheduler started. Waiting for scheduled tasks...")
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    main()