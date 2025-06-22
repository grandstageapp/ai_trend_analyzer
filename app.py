import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import markdown

# Configure logging with reduced verbosity for deployment
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Ultra-fast database configuration for deployment
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://localhost/ai_trends")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 1,            # Minimal for fastest startup
        "max_overflow": 2,         # Minimal for fastest startup
        "pool_recycle": 3600,      # 1 hour
        "pool_pre_ping": False,    # Skip ping for faster startup
        "pool_timeout": 10,        # Fast timeout
        "echo": False,
        "connect_args": {"connect_timeout": 5}  # Fast connection timeout
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    
    with app.app_context():
        # Import models to ensure tables are defined
        import models
        
        # Initialize database with minimal operations for deployment
        try:
            db.create_all()
        except Exception:
            # Continue without database for health checks
            pass
    
    # Register custom template filters
    from datetime import datetime
    
    @app.template_filter('days_ago')
    def days_ago_filter(date):
        """Calculate days ago from a given date"""
        if not date:
            return 0
        delta = datetime.utcnow() - date
        return delta.days
    
    @app.template_filter('markdown')
    def markdown_filter(text):
        """Convert Markdown text to HTML"""
        if not text:
            return ""
        return markdown.markdown(text, extensions=['nl2br'])
    

    
    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register performance monitoring routes
    try:
        from routes.performance import performance_bp
        app.register_blueprint(performance_bp)
        logger.info("Performance monitoring routes registered")
    except ImportError as e:
        logger.warning(f"Performance routes not available: {e}")
    

    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return "Page not found", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {error}")
        return "Internal server error", 500
    
    logger.info("AI Trends Analyzer application created successfully")
    return app
