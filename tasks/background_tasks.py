import logging
from datetime import datetime, timedelta
from typing import List
from app import db, create_app
from models import Post, Author, Engagement, TrendScore
from services.twitter_service import TwitterService
from services.trend_service import TrendService
from config import Config

logger = logging.getLogger(__name__)

class BackgroundTasks:
    """Background tasks for data fetching and processing"""
    
    def __init__(self):
        self.twitter_service = TwitterService()
        self.trend_service = TrendService()
        self.config = Config()
    
    def fetch_and_process_posts(self) -> None:
        """
        Main background task to fetch posts from Twitter and process them
        This should be run every 24 hours
        """
        with create_app().app_context():
            try:
                logger.info("Starting background task: fetch and process posts")
                
                # Skip rate limit check to avoid consuming quota
                # The search_recent_posts function will handle rate limiting internally
                
                # Fetch recent posts from Twitter
                search_terms = self.config.AI_SEARCH_TERMS[:self.config.SEARCH_TERMS_LIMIT]
                logger.info(f"Fetching posts with terms: {search_terms}...")
                posts_data = self.twitter_service.search_recent_posts(
                    search_terms=search_terms,
                    max_results=self.config.DEFAULT_SEARCH_RESULTS
                )
                
                logger.info(f"API returned {len(posts_data)} posts")
                
                if not posts_data:
                    logger.warning("No posts retrieved from Twitter API - checking if rate limited")
                    return
                
                # Log first post structure for debugging
                if posts_data:
                    logger.debug(f"Sample post keys: {list(posts_data[0].keys())}")
                    logger.debug(f"Sample post content: {posts_data[0].get('content', 'NO_CONTENT')[:100]}")
                
                # Store posts and authors in database
                logger.info("Starting database storage...")
                stored_posts = self._store_posts_and_authors(posts_data)
                logger.info(f"Database storage completed: {len(stored_posts)} posts stored")
                
                if stored_posts:
                    # Analyze trends from new posts
                    logger.info("Starting trend analysis...")
                    self._analyze_and_create_trends(stored_posts)
                    
                    # Calculate trend scores
                    logger.info("Calculating trend scores...")
                    self.trend_service.calculate_trend_scores()
                
                db.session.commit()
                logger.info(f"Background task completed successfully. Processed {len(stored_posts)} new posts")
                
            except Exception as e:
                logger.error(f"Error in background task: {e}")
                db.session.rollback()
    
    def daily_trend_analysis(self) -> None:
        """
        Daily task to recalculate trend scores and perform deep analysis
        This should be run every 24 hours
        """
        with create_app().app_context():
            try:
                logger.info("Starting daily trend analysis")
                
                # Get posts from the last 24 hours
                yesterday = datetime.utcnow() - timedelta(hours=24)
                recent_posts = Post.query.filter(
                    Post.created_at >= yesterday
                ).all()
                
                if recent_posts:
                    # Re-analyze trends with fresh data
                    self._analyze_and_create_trends(recent_posts)
                
                # Recalculate all trend scores
                self.trend_service.calculate_trend_scores()
                
                # Clean up old data (optional)
                self._cleanup_old_data()
                
                logger.info("Daily trend analysis completed")
                
            except Exception as e:
                logger.error(f"Error in daily trend analysis: {e}")
                db.session.rollback()
    
    def _store_posts_and_authors(self, posts_data: List[dict]) -> List[Post]:
        """
        Store posts and authors in the database
        
        Args:
            posts_data: List of post dictionaries from Twitter API
            
        Returns:
            List of stored Post objects
        """
        stored_posts = []
        logger.info(f"Processing {len(posts_data)} posts for storage")
        
        try:
            for i, post_data in enumerate(posts_data):
                logger.debug(f"Processing post {i+1}/{len(posts_data)}: {post_data.get('post_id', 'NO_ID')}")
                
                # Validate post data structure
                required_fields = ['post_id', 'content', 'created_at', 'author', 'metrics']
                missing_fields = [field for field in required_fields if field not in post_data]
                if missing_fields:
                    logger.warning(f"Skipping post due to missing fields: {missing_fields}")
                    continue
                
                # Check if post already exists
                existing_post = Post.query.filter_by(
                    post_id=post_data['post_id']
                ).first()
                
                if existing_post:
                    # Update engagement metrics for existing post
                    self._update_post_engagement(existing_post, post_data['metrics'])
                    continue
                
                # Get or create author
                author = self._get_or_create_author(post_data['author'])
                
                if not author:
                    continue
                
                # Create new post
                post = Post()
                post.post_id = post_data['post_id']
                post.author_id = author.id
                post.content = post_data['content']
                post.publish_date = post_data['created_at']
                post.created_at = datetime.utcnow()
                
                db.session.add(post)
                db.session.flush()  # Get the post ID
                
                # Create engagement record
                engagement = Engagement()
                engagement.post_id = post.id
                engagement.like_count = post_data['metrics']['like_count']
                engagement.comment_count = post_data['metrics']['reply_count']
                engagement.repost_count = (post_data['metrics']['retweet_count'] + 
                                         post_data['metrics'].get('quote_count', 0))
                engagement.timestamp = datetime.utcnow()
                
                db.session.add(engagement)
                stored_posts.append(post)
            
            db.session.commit()
            logger.info(f"Stored {len(stored_posts)} new posts")
            return stored_posts
            
        except Exception as e:
            logger.error(f"Error storing posts: {e}")
            db.session.rollback()
            return []
    
    def _get_or_create_author(self, author_data: dict) -> Author | None:
        """
        Get existing author or create new one
        
        Args:
            author_data: Author information from Twitter API
            
        Returns:
            Author object or None
        """
        try:
            username = author_data.get('username')
            if not username:
                return None
            
            # Check if author exists
            author = Author.query.filter_by(username=username).first()
            
            if author:
                # Update author information
                author.author_name = author_data.get('name', author.author_name)
                author.follower_count = author_data.get('follower_count', author.follower_count)
                author.verified = author_data.get('verified', author.verified)
                author.updated_at = datetime.utcnow()
            else:
                # Create new author
                author = Author()
                author.username = username
                author.author_name = author_data.get('name', '')
                author.profile_url = author_data.get('profile_url', '')
                author.follower_count = author_data.get('follower_count', 0)
                author.verified = author_data.get('verified', False)
                author.created_at = datetime.utcnow()
                db.session.add(author)
            
            return author
            
        except Exception as e:
            logger.error(f"Error handling author {author_data.get('username', 'unknown')}: {e}")
            return None
    
    def _update_post_engagement(self, post: Post, metrics: dict) -> None:
        """
        Update engagement metrics for an existing post
        
        Args:
            post: Post object to update
            metrics: New engagement metrics
        """
        try:
            engagement = Engagement(
                post_id=post.id,
                like_count=metrics['like_count'],
                comment_count=metrics['reply_count'],
                repost_count=metrics['retweet_count'] + metrics.get('quote_count', 0),
                timestamp=datetime.utcnow()
            )
            
            db.session.add(engagement)
            logger.debug(f"Updated engagement for post {post.post_id}")
            
        except Exception as e:
            logger.error(f"Error updating engagement for post {post.post_id}: {e}")
    
    def _analyze_and_create_trends(self, posts: List[Post]) -> None:
        """
        Analyze posts and create/update trends
        
        Args:
            posts: List of Post objects to analyze
        """
        try:
            if not posts:
                return
            
            trends = self.trend_service.analyze_and_create_trends(posts)
            logger.info(f"Created/updated {len(trends)} trends from {len(posts)} posts")
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
    
    def _cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """
        Clean up old data to prevent database bloat
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old engagement records (keep latest for each post)
            old_engagements = db.session.query(Engagement).filter(
                Engagement.timestamp < cutoff_date
            ).subquery()
            
            # Keep only the most recent engagement record per post
            latest_engagements = db.session.query(
                Engagement.post_id,
                db.func.max(Engagement.timestamp).label('latest_timestamp')
            ).group_by(Engagement.post_id).subquery()
            
            engagements_to_delete = db.session.query(Engagement).join(
                old_engagements, Engagement.id == old_engagements.c.id
            ).outerjoin(
                latest_engagements,
                (Engagement.post_id == latest_engagements.c.post_id) &
                (Engagement.timestamp == latest_engagements.c.latest_timestamp)
            ).filter(
                latest_engagements.c.post_id.is_(None)
            )
            
            deleted_count = engagements_to_delete.delete(synchronize_session=False)
            
            # Delete old trend scores (keep last 30 days)
            old_trend_scores = TrendScore.query.filter(
                TrendScore.date_generated < cutoff_date
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old engagement records and {old_trend_scores} old trend scores")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            db.session.rollback()

# Convenience functions for scheduling
def run_fetch_posts_task():
    """Run the fetch posts background task"""
    task_runner = BackgroundTasks()
    task_runner.fetch_and_process_posts()

def run_daily_analysis_task():
    """Run the daily trend analysis task"""
    task_runner = BackgroundTasks()
    task_runner.daily_trend_analysis()
