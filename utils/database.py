import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    def execute_sql_file(file_path: str) -> bool:
        """
        Execute SQL statements from a file
        
        Args:
            file_path: Path to SQL file
            
        Returns:
            Success status
        """
        try:
            with open(file_path, 'r') as file:
                sql_content = file.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                db.session.execute(text(statement))
            
            db.session.commit()
            logger.info(f"Successfully executed SQL file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing SQL file {file_path}: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def setup_pgvector() -> bool:
        """
        Set up PGVector extension and configure for hybrid search
        
        Returns:
            Success status
        """
        try:
            # Enable vector extension
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
            # Enable full-text search (should already be available)
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            
            # Create indexes for better performance
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_posts_content_fts 
                ON posts USING gin(to_tsvector('english', content));
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_posts_content_trgm 
                ON posts USING gin(content gin_trgm_ops);
            """))
            
            # Create function for hybrid search
            db.session.execute(text("""
                CREATE OR REPLACE FUNCTION hybrid_search_posts(
                    query_text TEXT,
                    query_vector VECTOR(1536),
                    limit_count INTEGER DEFAULT 10
                )
                RETURNS TABLE(
                    post_id INTEGER,
                    content TEXT,
                    fts_rank REAL,
                    vector_similarity REAL,
                    combined_score REAL
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        p.id,
                        p.content,
                        ts_rank(to_tsvector('english', p.content), plainto_tsquery('english', query_text)) as fts_rank,
                        1 - (p.embedding::vector <=> query_vector) as vector_similarity,
                        (ts_rank(to_tsvector('english', p.content), plainto_tsquery('english', query_text)) * 0.3 + 
                         (1 - (p.embedding::vector <=> query_vector)) * 0.7) as combined_score
                    FROM posts p
                    WHERE 
                        to_tsvector('english', p.content) @@ plainto_tsquery('english', query_text)
                        OR p.embedding IS NOT NULL
                    ORDER BY combined_score DESC
                    LIMIT limit_count;
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            db.session.commit()
            logger.info("PGVector setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up PGVector: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def vector_similarity_search(query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search on posts
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            
        Returns:
            List of similar posts with similarity scores
        """
        try:
            # Convert vector to string format for PostgreSQL
            vector_str = '[' + ','.join(map(str, query_vector)) + ']'
            
            query = text("""
                SELECT 
                    p.id,
                    p.post_id,
                    p.content,
                    p.publish_date,
                    a.username,
                    a.author_name,
                    1 - (p.embedding::vector <=> :query_vector::vector) as similarity
                FROM posts p
                JOIN authors a ON p.author_id = a.id
                WHERE p.embedding IS NOT NULL
                ORDER BY p.embedding::vector <=> :query_vector::vector
                LIMIT :limit_count;
            """)
            
            result = db.session.execute(query, {
                'query_vector': vector_str,
                'limit_count': limit
            })
            
            posts = []
            for row in result:
                posts.append({
                    'id': row.id,
                    'post_id': row.post_id,
                    'content': row.content,
                    'publish_date': row.publish_date,
                    'author_username': row.username,
                    'author_name': row.author_name,
                    'similarity': float(row.similarity)
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}")
            return []
    
    @staticmethod
    def hybrid_search(query_text: str, query_vector: Optional[List[float]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining full-text and vector similarity
        
        Args:
            query_text: Text query for full-text search
            query_vector: Optional vector for similarity search
            limit: Number of results to return
            
        Returns:
            List of search results with combined scores
        """
        try:
            if query_vector:
                vector_str = '[' + ','.join(map(str, query_vector)) + ']'
                
                query = text("""
                    SELECT * FROM hybrid_search_posts(:query_text, :query_vector::vector, :limit_count);
                """)
                
                result = db.session.execute(query, {
                    'query_text': query_text,
                    'query_vector': vector_str,
                    'limit_count': limit
                })
            else:
                # Fall back to full-text search only
                query = text("""
                    SELECT 
                        p.id as post_id,
                        p.content,
                        ts_rank(to_tsvector('english', p.content), plainto_tsquery('english', :query_text)) as fts_rank,
                        0.0 as vector_similarity,
                        ts_rank(to_tsvector('english', p.content), plainto_tsquery('english', :query_text)) as combined_score
                    FROM posts p
                    WHERE to_tsvector('english', p.content) @@ plainto_tsquery('english', :query_text)
                    ORDER BY combined_score DESC
                    LIMIT :limit_count;
                """)
                
                result = db.session.execute(query, {
                    'query_text': query_text,
                    'limit_count': limit
                })
            
            results = []
            for row in result:
                results.append({
                    'post_id': row.post_id,
                    'content': row.content,
                    'fts_rank': float(row.fts_rank),
                    'vector_similarity': float(row.vector_similarity),
                    'combined_score': float(row.combined_score)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    @staticmethod
    def get_database_stats() -> Dict[str, Any]:
        """
        Get database statistics for monitoring
        
        Returns:
            Dictionary of database statistics
        """
        try:
            stats = {}
            
            # Table counts
            from models import Post, Author, Engagement, Trend, PostTrend, TrendScore
            
            stats['posts_count'] = Post.query.count()
            stats['authors_count'] = Author.query.count()
            stats['engagements_count'] = Engagement.query.count()
            stats['trends_count'] = Trend.query.count()
            stats['post_trends_count'] = PostTrend.query.count()
            stats['trend_scores_count'] = TrendScore.query.count()
            
            # Recent activity
            from datetime import datetime, timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            stats['posts_last_24h'] = Post.query.filter(Post.created_at >= yesterday).count()
            stats['trends_last_24h'] = Trend.query.filter(Trend.created_at >= yesterday).count()
            
            # Database size (PostgreSQL specific)
            result = db.session.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
            """))
            
            stats['database_size'] = result.scalar()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
