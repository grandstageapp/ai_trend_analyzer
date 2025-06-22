"""
Query optimization utilities for improved database performance
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timedelta
from app import db
from models import Post, Author, Trend, TrendScore, Engagement, PostTrend
from utils.caching import cached, cache_manager

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Optimized database queries with caching and batching"""
    
    @staticmethod
    @cached(ttl=1800, key_prefix="trending_posts")
    def get_trending_posts(days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending posts with optimized query and caching"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Optimized query with joins and aggregations
        query = db.session.query(
            Post.id,
            Post.post_id,
            Post.content,
            Post.publish_date,
            Author.username,
            Author.author_name,
            Author.verified,
            func.avg(Engagement.like_count).label('avg_likes'),
            func.avg(Engagement.comment_count).label('avg_comments'),
            func.avg(Engagement.repost_count).label('avg_reposts'),
            func.count(Engagement.id).label('engagement_count')
        ).join(
            Author, Post.author_id == Author.id
        ).join(
            Engagement, Post.id == Engagement.post_id
        ).filter(
            Post.publish_date >= cutoff_date
        ).group_by(
            Post.id, Post.post_id, Post.content, Post.publish_date,
            Author.username, Author.author_name, Author.verified
        ).order_by(
            func.avg(Engagement.like_count + Engagement.comment_count + Engagement.repost_count).desc()
        ).limit(limit)
        
        results = []
        for row in query.all():
            results.append({
                'id': row.id,
                'post_id': row.post_id,
                'content': row.content,
                'publish_date': row.publish_date,
                'author': {
                    'username': row.username,
                    'name': row.author_name,
                    'verified': row.verified
                },
                'metrics': {
                    'avg_likes': float(row.avg_likes or 0),
                    'avg_comments': float(row.avg_comments or 0),
                    'avg_reposts': float(row.avg_reposts or 0),
                    'engagement_count': row.engagement_count
                }
            })
        
        logger.info(f"Retrieved {len(results)} trending posts from last {days} days")
        return results
    
    @staticmethod
    @cached(ttl=3600, key_prefix="top_trends")
    def get_top_trends(limit: int = 20) -> List[Dict[str, Any]]:
        """Get top trends with latest scores and post counts"""
        # Subquery for latest trend scores
        latest_scores = db.session.query(
            TrendScore.trend_id,
            func.max(TrendScore.date_generated).label('latest_date')
        ).group_by(TrendScore.trend_id).subquery()
        
        # Main query with optimized joins
        query = db.session.query(
            Trend.id,
            Trend.title,
            Trend.description,
            Trend.total_posts,
            Trend.created_at,
            TrendScore.score,
            TrendScore.date_generated
        ).join(
            latest_scores, Trend.id == latest_scores.c.trend_id
        ).join(
            TrendScore, 
            (TrendScore.trend_id == Trend.id) & 
            (TrendScore.date_generated == latest_scores.c.latest_date)
        ).order_by(
            TrendScore.score.desc()
        ).limit(limit)
        
        results = []
        for row in query.all():
            results.append({
                'id': row.id,
                'title': row.title,
                'description': row.description,
                'total_posts': row.total_posts,
                'created_at': row.created_at,
                'latest_score': float(row.score),
                'last_updated': row.date_generated
            })
        
        logger.info(f"Retrieved {len(results)} top trends")
        return results
    
    @staticmethod
    @cached(ttl=1800, key_prefix="trend_details")
    def get_trend_with_posts(trend_id: int) -> Optional[Dict[str, Any]]:
        """Get trend details with related posts using optimized loading"""
        trend = db.session.query(Trend).options(
            selectinload(Trend.post_trends).selectinload(PostTrend.post).selectinload(Post.author),
            selectinload(Trend.trend_scores)
        ).filter(Trend.id == trend_id).first()
        
        if not trend:
            return None
        
        # Get recent posts for this trend
        recent_posts = db.session.query(Post).join(
            PostTrend, Post.id == PostTrend.post_id
        ).filter(
            PostTrend.trend_id == trend_id
        ).options(
            joinedload(Post.author),
            selectinload(Post.engagements)
        ).order_by(Post.publish_date.desc()).limit(10).all()
        
        # Format posts data
        posts_data = []
        for post in recent_posts:
            latest_engagement = post.engagements[-1] if post.engagements else None
            posts_data.append({
                'id': post.id,
                'post_id': post.post_id,
                'content': post.content,
                'publish_date': post.publish_date,
                'author': {
                    'username': post.author.username,
                    'name': post.author.author_name,
                    'verified': post.author.verified
                },
                'engagement': {
                    'likes': latest_engagement.like_count if latest_engagement else 0,
                    'comments': latest_engagement.comment_count if latest_engagement else 0,
                    'reposts': latest_engagement.repost_count if latest_engagement else 0
                } if latest_engagement else None
            })
        
        # Get trend score history
        score_history = []
        for score in sorted(trend.trend_scores, key=lambda x: x.date_generated)[-10:]:
            score_history.append({
                'date': score.date_generated,
                'score': float(score.score)
            })
        
        result = {
            'id': trend.id,
            'title': trend.title,
            'description': trend.description,
            'total_posts': trend.total_posts,
            'created_at': trend.created_at,
            'posts': posts_data,
            'score_history': score_history,
            'latest_score': score_history[-1]['score'] if score_history else 0.0
        }
        
        logger.info(f"Retrieved trend details for trend {trend_id} with {len(posts_data)} posts")
        return result
    
    @staticmethod
    @cached(ttl=3600, key_prefix="author_stats")
    def get_author_statistics(limit: int = 20) -> List[Dict[str, Any]]:
        """Get author statistics with post counts and engagement metrics"""
        query = db.session.query(
            Author.id,
            Author.username,
            Author.author_name,
            Author.verified,
            Author.follower_count,
            func.count(Post.id).label('post_count'),
            func.avg(Engagement.like_count).label('avg_likes'),
            func.avg(Engagement.comment_count).label('avg_comments'),
            func.avg(Engagement.repost_count).label('avg_reposts')
        ).join(
            Post, Author.id == Post.author_id
        ).join(
            Engagement, Post.id == Engagement.post_id
        ).group_by(
            Author.id, Author.username, Author.author_name, 
            Author.verified, Author.follower_count
        ).having(
            func.count(Post.id) > 0
        ).order_by(
            func.avg(Engagement.like_count + Engagement.comment_count + Engagement.repost_count).desc()
        ).limit(limit)
        
        results = []
        for row in query.all():
            results.append({
                'id': row.id,
                'username': row.username,
                'name': row.author_name,
                'verified': row.verified,
                'follower_count': row.follower_count,
                'post_count': row.post_count,
                'avg_engagement': {
                    'likes': float(row.avg_likes or 0),
                    'comments': float(row.avg_comments or 0),
                    'reposts': float(row.avg_reposts or 0)
                }
            })
        
        logger.info(f"Retrieved statistics for {len(results)} top authors")
        return results
    
    @staticmethod
    def invalidate_trend_caches(trend_id: Optional[int] = None):
        """Invalidate trend-related caches"""
        patterns = ["top_trends*", "trending_posts*"]
        if trend_id:
            patterns.append(f"trend_details*{trend_id}*")
        
        for pattern in patterns:
            cache_manager.clear_pattern(pattern)
        
        logger.info(f"Invalidated trend caches for trend_id: {trend_id}")
    
    @staticmethod
    def get_database_performance_stats() -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            # Query execution statistics
            stats_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                ORDER BY seq_scan + idx_scan DESC
            """)
            
            table_stats = db.session.execute(stats_query).fetchall()
            
            # Index usage statistics
            index_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public' AND idx_scan > 0
                ORDER BY idx_scan DESC
                LIMIT 10
            """)
            
            index_stats = db.session.execute(index_query).fetchall()
            
            return {
                'table_stats': [dict(row._mapping) for row in table_stats],
                'index_stats': [dict(row._mapping) for row in index_stats],
                'cache_stats': cache_manager.get_stats()
            }
            
        except Exception as e:
            logger.error(f"Error getting database performance stats: {e}")
            return {'error': str(e), 'cache_stats': cache_manager.get_stats()}

# Global query optimizer instance
query_optimizer = QueryOptimizer()