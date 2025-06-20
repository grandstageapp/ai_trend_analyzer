import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, flash
from sqlalchemy import desc, asc, func, or_
from models import db, Trend, Post, Author, Engagement, TrendScore, PostTrend
from services.openai_service import OpenAIService
from utils.helpers import format_number, truncate_text

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage displaying trend cards with search and filtering"""
    # Get query parameters
    search_query = request.args.get('search', '').strip()
    date_filter = request.args.get('date_filter', 'all')
    sort_order = request.args.get('sort', 'score_desc')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Base query
    query = Trend.query
    
    # Apply search filter
    if search_query:
        query = query.filter(
            or_(
                Trend.title.ilike(f'%{search_query}%'),
                Trend.description.ilike(f'%{search_query}%')
            )
        )
    
    # Apply date filter
    if date_filter == 'today':
        today = datetime.utcnow().date()
        query = query.filter(func.date(Trend.created_at) == today)
    elif date_filter == 'week':
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Trend.created_at >= week_ago)
    elif date_filter == 'month':
        month_ago = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Trend.created_at >= month_ago)
    
    # Apply sorting
    if sort_order == 'score_desc':
        # Join with latest trend scores for sorting
        subquery = db.session.query(
            TrendScore.trend_id,
            func.max(TrendScore.date_generated).label('latest_date')
        ).group_by(TrendScore.trend_id).subquery()
        
        latest_scores = db.session.query(
            TrendScore.trend_id,
            TrendScore.score
        ).join(
            subquery,
            (TrendScore.trend_id == subquery.c.trend_id) &
            (TrendScore.date_generated == subquery.c.latest_date)
        ).subquery()
        
        query = query.outerjoin(latest_scores, Trend.id == latest_scores.c.trend_id).order_by(
            desc(latest_scores.c.score), desc(Trend.created_at)
        )
    elif sort_order == 'score_asc':
        # Similar to above but ascending
        subquery = db.session.query(
            TrendScore.trend_id,
            func.max(TrendScore.date_generated).label('latest_date')
        ).group_by(TrendScore.trend_id).subquery()
        
        latest_scores = db.session.query(
            TrendScore.trend_id,
            TrendScore.score
        ).join(
            subquery,
            (TrendScore.trend_id == subquery.c.trend_id) &
            (TrendScore.date_generated == subquery.c.latest_date)
        ).subquery()
        
        query = query.outerjoin(latest_scores, Trend.id == latest_scores.c.trend_id).order_by(
            asc(latest_scores.c.score), desc(Trend.created_at)
        )
    elif sort_order == 'newest':
        query = query.order_by(desc(Trend.created_at))
    elif sort_order == 'oldest':
        query = query.order_by(asc(Trend.created_at))
    
    # Paginate results
    trends_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    trends = trends_pagination.items
    
    # Prepare trend data with scores and summaries
    trend_data = []
    for trend in trends:
        score_history = trend.get_score_history(7)
        trend_data.append({
            'trend': trend,
            'latest_score': trend.get_latest_score(),
            'score_history': score_history,
            'summary': truncate_text(trend.description, 2) if trend.description else ''
        })
    
    return render_template('index.html', 
                         trends=trend_data,
                         pagination=trends_pagination,
                         search_query=search_query,
                         date_filter=date_filter,
                         sort_order=sort_order)

@main_bp.route('/trend/<int:trend_id>')
def trend_detail(trend_id):
    """Individual trend page with detailed information and chat interface"""
    trend = Trend.query.get_or_404(trend_id)
    
    # Get trend score history
    score_history = trend.get_score_history(30)  # Last 30 days
    
    # Get related posts
    related_posts = db.session.query(Post).join(PostTrend).filter(
        PostTrend.trend_id == trend_id
    ).order_by(desc(Post.publish_date)).limit(10).all()
    
    # Get engagement statistics
    total_engagement = db.session.query(
        func.sum(Engagement.like_count).label('total_likes'),
        func.sum(Engagement.comment_count).label('total_comments'),
        func.sum(Engagement.repost_count).label('total_reposts')
    ).join(Post).join(PostTrend).filter(
        PostTrend.trend_id == trend_id
    ).first()
    
    return render_template('trend_detail.html',
                         trend=trend,
                         score_history=score_history,
                         related_posts=related_posts,
                         total_engagement=total_engagement)

@main_bp.route('/api/chat', methods=['POST'])
def chat():
    """AI chat interface for trend questions"""
    try:
        data = request.get_json()
        trend_id = data.get('trend_id')
        message = data.get('message', '').strip()
        
        if not trend_id or not message:
            return jsonify({'error': 'Missing trend_id or message'}), 400
        
        trend = Trend.query.get_or_404(trend_id)
        
        # Get related posts for context
        related_posts = db.session.query(Post).join(PostTrend).filter(
            PostTrend.trend_id == trend_id
        ).limit(5).all()
        
        # Prepare context
        context = f"Trend: {trend.title}\n"
        context += f"Description: {trend.description}\n"
        context += "Related posts:\n"
        for post in related_posts:
            context += f"- {post.content[:200]}...\n"
        
        # Get AI response
        openai_service = OpenAIService()
        response = openai_service.chat_about_trend(context, message)
        
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Failed to process chat message'}), 500

@main_bp.route('/api/generate-content', methods=['POST'])
def generate_content():
    """Generate sample blog content for a trend"""
    try:
        data = request.get_json()
        trend_id = data.get('trend_id')
        
        if not trend_id:
            return jsonify({'error': 'Missing trend_id'}), 400
        
        trend = Trend.query.get_or_404(trend_id)
        
        # Get related posts for context
        related_posts = db.session.query(Post).join(PostTrend).filter(
            PostTrend.trend_id == trend_id
        ).limit(10).all()
        
        # Prepare context
        context = f"Trend: {trend.title}\n"
        context += f"Description: {trend.description}\n"
        context += "Key points from social media discussions:\n"
        for post in related_posts[:5]:
            context += f"- {post.content[:150]}...\n"
        
        # Generate content
        openai_service = OpenAIService()
        blog_content = openai_service.generate_blog_content(context)
        
        return jsonify({'content': blog_content})
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return jsonify({'error': 'Failed to generate content'}), 500

@main_bp.route('/api/search-trends')
def search_trends():
    """HTMX endpoint for live trend search"""
    search_query = request.args.get('search', '').strip()
    
    if not search_query:
        return render_template('components/trend_card.html', trends=[])
    
    trends = Trend.query.filter(
        or_(
            Trend.title.ilike(f'%{search_query}%'),
            Trend.description.ilike(f'%{search_query}%')
        )
    ).limit(10).all()
    
    # Prepare trend data
    trend_data = []
    for trend in trends:
        score_history = trend.get_score_history(7)
        trend_data.append({
            'trend': trend,
            'latest_score': trend.get_latest_score(),
            'score_history': score_history,
            'summary': truncate_text(trend.description, 2) if trend.description else ''
        })
    
    return render_template('components/trend_card.html', trends=trend_data)
