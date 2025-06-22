from flask import Flask, jsonify
import logging
import os

# Configure minimal logging for fastest startup
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key")

# Add immediate health endpoints first
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

@app.route('/ping')
def ping():
    return {'status': 'ok'}, 200

# Load full application components immediately but efficiently
try:
    # Import and setup database components
    from werkzeug.middleware.proxy_fix import ProxyFix
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.orm import DeclarativeBase
    import markdown

    class Base(DeclarativeBase):
        pass

    db = SQLAlchemy(model_class=Base)
    
    # Minimal database config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://localhost/ai_trends")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "echo": False}
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    db.init_app(app)
    
    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    try:
        from routes.performance import performance_bp
        app.register_blueprint(performance_bp)
    except ImportError:
        pass
    
    # Add template filters
    @app.template_filter('days_ago')
    def days_ago_filter(date):
        if not date:
            return 0
        from datetime import datetime
        delta = datetime.utcnow() - date
        return delta.days
    
    @app.template_filter('markdown')
    def markdown_filter(text):
        if not text:
            return ""
        return markdown.markdown(text, extensions=['nl2br'])
    
    # Initialize database on first use
    @app.before_first_request
    def init_db():
        try:
            with app.app_context():
                import models
                db.create_all()
                with db.engine.connect() as conn:
                    conn.execute(db.text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
        except:
            pass
    
except Exception as e:
    logger.error(f"App setup error: {e}")



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
