import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy import func, desc
from app import db
from models import Post, Author, Engagement, Trend, PostTrend, TrendScore
from services.openai_service import OpenAIService
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class TrendService:
    """Service for trend analysis and scoring"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def analyze_and_create_trends(self, posts: List[Post]) -> List[Trend]:
        """
        Analyze posts and create trends using clustering and AI
        
        Args:
            posts: List of Post objects to analyze
            
        Returns:
            List of created Trend objects
        """
        try:
            if not posts:
                logger.info("No posts to analyze for trends")
                return []
            
            logger.info(f"Analyzing {len(posts)} posts for trends")
            
            # Step 1: Generate embeddings for posts
            post_texts = [post.content for post in posts]
            embeddings = self.openai_service.generate_embeddings(post_texts)
            
            if not embeddings:
                logger.error("Failed to generate embeddings")
                return []
            
            # Step 2: Cluster posts by similarity
            clusters = self._cluster_posts(embeddings, posts)
            
            # Step 3: Use OpenAI to identify trends from clusters
            trends = []
            for cluster_posts in clusters:
                if len(cluster_posts) < 2:  # Skip single-post clusters
                    continue
                
                cluster_data = [{'content': post.content} for post in cluster_posts]
                identified_trends = self.openai_service.cluster_and_identify_trends(cluster_data)
                
                for trend_data in identified_trends:
                    # Create trend with basic description only
                    trend = self._create_trend_basic(trend_data, cluster_posts)
                    if trend:
                        trends.append(trend)
            
            logger.info(f"Created {len(trends)} trends")
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return []
    
    def calculate_trend_scores(self) -> None:
        """
        Calculate trend scores for all trends based on engagement metrics
        Formula: (Total Likes + (Total Comments * 1.1) + (Total Reposts * 1.2)) / Total Followers
        """
        try:
            trends = Trend.query.all()
            logger.info(f"Calculating scores for {len(trends)} trends")
            
            for trend in trends:
                score = self._calculate_single_trend_score(trend)
                
                # Store the score
                trend_score = TrendScore(
                    trend_id=trend.id,
                    score=score,
                    date_generated=datetime.utcnow()
                )
                
                db.session.add(trend_score)
            
            db.session.commit()
            logger.info("Trend scores calculated and saved")
            
        except Exception as e:
            logger.error(f"Error calculating trend scores: {e}")
            db.session.rollback()
    
    def _cluster_posts(self, embeddings: List[List[float]], posts: List[Post]) -> List[List[Post]]:
        """
        Cluster posts using K-means clustering on embeddings
        
        Args:
            embeddings: List of embedding vectors
            posts: Corresponding list of Post objects
            
        Returns:
            List of post clusters
        """
        try:
            if len(posts) < 3:
                return [posts]  # Return all posts as single cluster if too few
            
            # Convert embeddings to numpy array
            X = np.array(embeddings)
            
            # Determine optimal number of clusters (between 2 and min(8, len(posts)//2))
            n_clusters = min(8, max(2, len(posts) // 3))
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)
            
            # Group posts by cluster
            clusters = [[] for _ in range(n_clusters)]
            for i, label in enumerate(cluster_labels):
                clusters[label].append(posts[i])
            
            # Filter out empty clusters
            clusters = [cluster for cluster in clusters if cluster]
            
            logger.info(f"Clustered {len(posts)} posts into {len(clusters)} clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering posts: {e}")
            return [posts]  # Return all posts as single cluster on error
    
    def _create_trend_basic(self, trend_data: Dict[str, Any], cluster_posts: List[Post]) -> Trend:
        """
        Create a Trend object with basic information only (no description)
        
        Args:
            trend_data: Trend information from OpenAI
            cluster_posts: Posts that belong to this trend
            
        Returns:
            Created Trend object or None
        """
        try:
            title = trend_data.get('title', '').strip()
            if not title:
                return None
            
            # Check if trend already exists
            existing_trend = Trend.query.filter_by(title=title).first()
            if existing_trend:
                logger.info(f"Trend '{title}' already exists, updating...")
                trend = existing_trend
            else:
                # Create new trend with basic description
                trend = Trend(
                    title=title,
                    description=f"Trending topic: {title}",
                    total_posts=len(cluster_posts)
                )
                db.session.add(trend)
                db.session.flush()  # Get the ID
            
            trend.total_posts = len(cluster_posts)
            trend.updated_at = datetime.utcnow()
            
            # Create post-trend relationships
            for post in cluster_posts:
                existing_relation = PostTrend.query.filter_by(
                    post_id=post.id, 
                    trend_id=trend.id
                ).first()
                
                if not existing_relation:
                    post_trend = PostTrend(
                        post_id=post.id,
                        trend_id=trend.id
                    )
                    db.session.add(post_trend)
            
            db.session.commit()
            logger.info(f"Created/updated trend: {title}")
            return trend
            
        except Exception as e:
            logger.error(f"Error creating trend: {e}")
            db.session.rollback()
            return None

    def _create_trend_from_data(self, trend_data: Dict[str, Any], cluster_posts: List[Post]) -> Trend:
        """
        Create a Trend object from AI-identified trend data
        
        Args:
            trend_data: Trend information from OpenAI
            cluster_posts: Posts that belong to this trend
            
        Returns:
            Created Trend object or None
        """
        try:
            title = trend_data.get('title', '').strip()
            if not title:
                return None
            
            # Check if trend already exists
            existing_trend = Trend.query.filter_by(title=title).first()
            if existing_trend:
                logger.info(f"Trend '{title}' already exists, updating...")
                trend = existing_trend
            else:
                # Create new trend
                trend = Trend(
                    title=title,
                    total_posts=len(cluster_posts)
                )
                db.session.add(trend)
                db.session.flush()  # Get the ID
            
            # Generate detailed description
            post_contents = [post.content for post in cluster_posts]
            description = self.openai_service.generate_trend_description(title, post_contents)
            trend.description = description
            trend.total_posts = len(cluster_posts)
            trend.updated_at = datetime.utcnow()
            
            # Create post-trend relationships
            for post in cluster_posts:
                existing_relation = PostTrend.query.filter_by(
                    post_id=post.id, 
                    trend_id=trend.id
                ).first()
                
                if not existing_relation:
                    post_trend = PostTrend(
                        post_id=post.id,
                        trend_id=trend.id
                    )
                    db.session.add(post_trend)
            
            db.session.commit()
            logger.info(f"Created/updated trend: {title}")
            return trend
            
        except Exception as e:
            logger.error(f"Error creating trend: {e}")
            db.session.rollback()
            return None
    
    def _calculate_single_trend_score(self, trend: Trend) -> float:
        """
        Calculate score for a single trend
        
        Args:
            trend: Trend object to calculate score for
            
        Returns:
            Calculated trend score
        """
        try:
            # Get all posts related to this trend with their latest engagement
            posts_engagement = db.session.query(
                Post, Engagement, Author
            ).join(
                PostTrend, Post.id == PostTrend.post_id
            ).join(
                Author, Post.author_id == Author.id
            ).outerjoin(
                Engagement, Post.id == Engagement.post_id
            ).filter(
                PostTrend.trend_id == trend.id
            ).all()
            
            if not posts_engagement:
                return 0.0
            
            total_likes = 0
            total_comments = 0
            total_reposts = 0
            total_followers = 0
            
            # Aggregate engagement data
            for post, engagement, author in posts_engagement:
                if engagement:
                    total_likes += engagement.like_count
                    total_comments += engagement.comment_count
                    total_reposts += engagement.repost_count
                
                total_followers += author.follower_count
            
            # Avoid division by zero
            if total_followers == 0:
                total_followers = 1
            
            # Calculate weighted score
            # Formula: (Total Likes + (Total Comments * 1.1) + (Total Reposts * 1.2)) / Total Followers
            weighted_engagement = (
                total_likes + 
                (total_comments * 1.1) + 
                (total_reposts * 1.2)
            )
            
            score = weighted_engagement / total_followers
            
            # Scale score to make it more readable (multiply by 1000)
            score = round(score * 1000, 2)
            
            logger.debug(f"Trend '{trend.title}' score: {score}")
            return score
            
        except Exception as e:
            logger.error(f"Error calculating score for trend {trend.id}: {e}")
            return 0.0
    
    def get_trending_topics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get summary of trending topics over the specified time period
        
        Args:
            days: Number of days to look back
            
        Returns:
            Summary statistics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get trends created in the time period
            recent_trends = Trend.query.filter(
                Trend.created_at >= since_date
            ).count()
            
            # Get total posts analyzed
            total_posts = Post.query.filter(
                Post.created_at >= since_date
            ).count()
            
            # Get top trending topics by latest score
            top_trends = db.session.query(Trend, TrendScore.score).join(
                TrendScore, Trend.id == TrendScore.trend_id
            ).filter(
                TrendScore.date_generated >= since_date
            ).order_by(
                desc(TrendScore.score)
            ).limit(5).all()
            
            return {
                'period_days': days,
                'recent_trends_count': recent_trends,
                'total_posts_analyzed': total_posts,
                'top_trends': [
                    {
                        'title': trend.title,
                        'score': score,
                        'posts_count': trend.total_posts
                    }
                    for trend, score in top_trends
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting trending topics summary: {e}")
            return {}
