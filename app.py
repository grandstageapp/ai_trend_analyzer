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
    
    # Database configuration with improved connection pooling
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://localhost/ai_trends")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 20,           # Number of connections to maintain
        "max_overflow": 30,        # Additional connections beyond pool_size
        "pool_recycle": 3600,      # Recycle connections every hour
        "pool_pre_ping": True,     # Verify connections before use
        "pool_timeout": 30,        # Timeout for getting connection from pool
        "echo": False,             # Set to True for SQL debugging
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    
    with app.app_context():
        # Import models to ensure tables are created
        import models
        
        # Initialize database with faster configuration for deployment
        try:
            db.create_all()
            # Enable PGVector extension
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
            except Exception as e:
                pass  # Continue without extension for faster startup
        except Exception as e:
            pass  # Continue for health checks even if DB fails initially
    
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
