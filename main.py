from flask import Flask, jsonify
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app with immediate health endpoints
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Critical: Add immediate root endpoint for deployment health checks
@app.route('/')
def root():
    """Fastest possible root endpoint for deployment health checks"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-trends-analyzer',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Basic ping endpoint without dependencies
@app.route('/ping')
def ping():
    """Simple ping endpoint for load balancers"""
    return jsonify({'status': 'ok'}), 200

# Simple health endpoint without database
@app.route('/health')
def health():
    """Basic health check without dependencies"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-trends-analyzer',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Now load the full application with all features
try:
    logger.info("Loading full application...")
    from app import create_app
    full_app = create_app()
    
    # Register all blueprints from full app
    for blueprint_name, blueprint in full_app.blueprints.items():
        if blueprint_name not in app.blueprints:
            app.register_blueprint(blueprint)
            logger.info(f"Registered blueprint: {blueprint_name}")
    
    # Copy template filters and other app context
    app.jinja_env.filters.update(full_app.jinja_env.filters)
    
    # Copy error handlers
    for code, handler in full_app.error_handler_spec.get(None, {}).items():
        if code not in app.error_handler_spec.get(None, {}):
            app.register_error_handler(code, handler)
    
    logger.info("Full application loaded successfully")
    
except Exception as e:
    logger.error(f"Failed to load full application: {e}")
    logger.info("Running in minimal mode with health checks only")

if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
