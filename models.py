from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
import uuid

class Author(db.Model):
    """X/Twitter authors table"""
    __tablename__ = 'authors'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    author_name = db.Column(db.String(200), nullable=True)
    profile_url = db.Column(db.String(500), nullable=True)
    follower_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True)
    
    def __repr__(self):
        return f'<Author {self.username}>'

class Post(db.Model):
    """X posts table"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(100), unique=True, nullable=False, index=True)  # X post ID
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vector embedding for similarity search
    embedding = db.Column(db.Text, nullable=True)  # Store as comma-separated values
    
    # Relationships
    engagements = db.relationship('Engagement', backref='post', lazy=True, cascade='all, delete-orphan')
    post_trends = db.relationship('PostTrend', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.post_id}>'

class Engagement(db.Model):
    """Engagement metrics for posts"""
    __tablename__ = 'engagement'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    repost_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Engagement {self.post_id} at {self.timestamp}>'

class Trend(db.Model):
    """Trends extracted from clustered posts"""
    __tablename__ = 'trends'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    total_posts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post_trends = db.relationship('PostTrend', backref='trend', lazy=True, cascade='all, delete-orphan')
    trend_scores = db.relationship('TrendScore', backref='trend', lazy=True, cascade='all, delete-orphan')
    
    def get_latest_score(self):
        """Get the most recent trend score"""
        latest_score = TrendScore.query.filter_by(trend_id=self.id).order_by(TrendScore.date_generated.desc()).first()
        return latest_score.score if latest_score else 0
    
    def get_score_history(self, days=7):
        """Get trend score history for the last N days"""
        scores = TrendScore.query.filter_by(trend_id=self.id).order_by(TrendScore.date_generated.desc()).limit(days).all()
        return [(score.date_generated, score.score) for score in reversed(scores)]
    
    def __repr__(self):
        return f'<Trend {self.title}>'

class PostTrend(db.Model):
    """Relationship between posts and trends"""
    __tablename__ = 'post_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    trend_id = db.Column(db.Integer, db.ForeignKey('trends.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique post-trend relationships
    __table_args__ = (db.UniqueConstraint('post_id', 'trend_id', name='unique_post_trend'),)
    
    def __repr__(self):
        return f'<PostTrend {self.post_id}-{self.trend_id}>'

class TrendScore(db.Model):
    """Trend scores calculated over time"""
    __tablename__ = 'trend_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    trend_id = db.Column(db.Integer, db.ForeignKey('trends.id'), nullable=False)
    date_generated = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<TrendScore {self.trend_id}: {self.score}>'
