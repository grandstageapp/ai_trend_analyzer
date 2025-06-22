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
    try:
        # Get query parameters
        search_query = request.args.get('search', '').strip()
        date_filter = request.args.get('date_filter', 'all')
        sort_order = request.args.get('sort', 'score_desc')
        page = request.args.get('page', 1, type=int)
        per_page = 50  # Show more trends per page to avoid pagination with few items
        
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
        
        # Prepare trend data with scores, summaries, and engagement data
        trend_data = []
        for trend in trends:
            score_history = trend.get_score_history(10)
            
            # Get actual post count and engagement data for this trend
            related_posts = db.session.query(Post).join(PostTrend).filter(
                PostTrend.trend_id == trend.id
            ).all()
            
            total_engagement = 0
            post_count = len(related_posts)
            
            for post in related_posts:
                latest_engagement = db.session.query(Engagement).filter_by(
                    post_id=post.id
                ).order_by(Engagement.timestamp.desc()).first()
                
                if latest_engagement:
                    total_engagement += (
                        latest_engagement.like_count + 
                        latest_engagement.comment_count + 
                        latest_engagement.repost_count
                    )
            
            trend_data.append({
                'trend': trend,
                'latest_score': trend.get_latest_score(),
                'score_history': score_history,
                'summary': truncate_text(trend.description, 2) if trend.description else '',
                'hover_summary': truncate_text(trend.description, 3) if trend.description else '',
                'post_count': post_count,
                'total_engagement': total_engagement
            })
        
        # Get total trends count for header display
        total_trends_count = Trend.query.count()
        
        return render_template('index.html', 
                             trends=trend_data,
                             total_trends_count=total_trends_count,
                             pagination=trends_pagination,
                             search_query=search_query,
                             date_filter=date_filter,
                             sort_order=sort_order)
    
    except Exception as e:
        logger.error(f"Error in homepage route: {e}")
        import traceback
        traceback.print_exc()
        # Return a simple error page or fallback
        total_trends_count = 0
        try:
            total_trends_count = Trend.query.count()
        except:
            pass
        
        return render_template('index.html', 
                             trends=[],
                             total_trends_count=total_trends_count,
                             pagination=None,
                             search_query='',
                             date_filter='all',
                             sort_order='score_desc',
                             error_message="Unable to load trends. Please try again later.")

@main_bp.route('/trend/<int:trend_id>')
def trend_detail(trend_id):
    """Individual trend page with detailed information and chat interface"""
    trend = Trend.query.get_or_404(trend_id)
    
    # Get trend score history
    score_history_raw = trend.get_score_history(10)  # Last 10 days
    # Convert datetime objects to strings for JSON serialization
    score_history = [[item[0].isoformat(), item[1]] for item in score_history_raw]
    
    # Get related posts
    related_posts = db.session.query(Post).join(PostTrend).filter(
        PostTrend.trend_id == trend_id
    ).order_by(desc(Post.publish_date)).limit(10).all()
    
    # Get engagement statistics from the latest engagement for each post
    total_engagement = db.session.query(
        func.sum(Engagement.like_count).label('total_likes'),
        func.sum(Engagement.comment_count).label('total_comments'),
        func.sum(Engagement.repost_count).label('total_reposts')
    ).join(Post).join(PostTrend).filter(
        PostTrend.trend_id == trend_id
    ).first()
    
    # Ensure we have valid engagement data
    if not total_engagement.total_likes:
        total_engagement = type('obj', (object,), {
            'total_likes': 0,
            'total_comments': 0,
            'total_reposts': 0
        })
    
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
        content_type = data.get('type', 'blog')  # blog, social, newsletter, outline
        
        if not trend_id:
            return jsonify({'error': 'Missing trend_id'}), 400
        
        # Generate content using dedicated service
        from services.content_generation_service import ContentGenerationService
        content_service = ContentGenerationService()
        
        if content_type == 'blog':
            content = content_service.generate_blog_content(trend_id)
        elif content_type == 'social':
            platform = data.get('platform', 'general')
            content = content_service.generate_social_media_content(trend_id, platform)
        elif content_type == 'newsletter':
            content = content_service.generate_email_newsletter_content(trend_id)
        elif content_type == 'outline':
            content = content_service.generate_content_outline(trend_id)
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        return jsonify({'content': content, 'type': content_type})
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return jsonify({'error': 'Failed to generate content'}), 500

@main_bp.route('/api/generate-social', methods=['POST'])
def generate_social_content():
    """Generate social media content for a trend"""
    try:
        data = request.get_json()
        trend_id = data.get('trend_id')
        platform = data.get('platform', 'general')
        
        if not trend_id:
            return jsonify({'error': 'Missing trend_id'}), 400
        
        from services.content_generation_service import ContentGenerationService
        content_service = ContentGenerationService()
        content = content_service.generate_social_media_content(trend_id, platform)
        
        return jsonify({'content': content, 'platform': platform})
        
    except Exception as e:
        logger.error(f"Error generating social content: {e}")
        return jsonify({'error': 'Failed to generate social content'}), 500

@main_bp.route('/api/generate-newsletter', methods=['POST'])
def generate_newsletter_content():
    """Generate newsletter content for a trend"""
    try:
        data = request.get_json()
        trend_id = data.get('trend_id')
        
        if not trend_id:
            return jsonify({'error': 'Missing trend_id'}), 400
        
        from services.content_generation_service import ContentGenerationService
        content_service = ContentGenerationService()
        content = content_service.generate_email_newsletter_content(trend_id)
        
        return jsonify({'content': content})
        
    except Exception as e:
        logger.error(f"Error generating newsletter content: {e}")
        return jsonify({'error': 'Failed to generate newsletter content'}), 500

@main_bp.route('/api/generate-outline', methods=['POST'])
def generate_content_outline():
    """Generate content outline for a trend"""
    try:
        data = request.get_json()
        trend_id = data.get('trend_id')
        
        if not trend_id:
            return jsonify({'error': 'Missing trend_id'}), 400
        
        from services.content_generation_service import ContentGenerationService
        content_service = ContentGenerationService()
        content = content_service.generate_content_outline(trend_id)
        
        return jsonify({'content': content})
        
    except Exception as e:
        logger.error(f"Error generating content outline: {e}")
        return jsonify({'error': 'Failed to generate content outline'}), 500

@main_bp.route('/api/search-trends')
def search_trends():
    """HTMX endpoint for live trend search with filters"""
    try:
        # Get all filter parameters
        search_query = request.args.get('search', '').strip()
        date_filter = request.args.get('date_filter', 'all')
        sort_order = request.args.get('sort', 'score_desc')
        
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
        
        # Limit results for HTMX
        trends = query.limit(12).all()
        
        # Prepare trend data
        trend_data = []
        for trend in trends:
            score_history = trend.get_score_history(7)
            trend_data.append({
                'trend': trend,
                'latest_score': trend.get_latest_score(),
                'score_history': score_history,
                'summary': truncate_text(trend.description, 2) if trend.description else '',
                'hover_summary': truncate_text(trend.description, 3) if trend.description else ''
            })
        
        return render_template('components/trend_card.html', trends=trend_data)
        
    except Exception as e:
        logger.error(f"Error in search_trends: {e}")
        return render_template('components/trend_card.html', trends=[])
